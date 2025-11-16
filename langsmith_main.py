#===main file to run service to perform veg dishes detection given input images

#=====================================================================
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional, Dict, Any, Set
import os
import json
from dotenv import load_dotenv
from utils.helper_functions import process_image_sync
import shutil
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import json
import asyncio
from utils.load_config import load_config
import uvicorn
#--import logger
from utils.logger_setup import get_logger

# --- LANGSMITH: Step 1: Import tracing components ---
from langsmith import Client, traceable
from langsmith.run_trees import get_current_run_tree

logger = get_logger(__name__)

#====================================
#--load config from config.yaml file
config = load_config()
logger.debug("--------------------------------")
logger.debug(f"config: {config}")
logger.debug("--------------------------------")
#====================================

#====================================
load_dotenv()
mcp_url = config["mcp_url"]
logger.debug(f"mcp_url: {mcp_url}")
logger.debug("--------------------------------")

# --- LANGSMITH: Step 2: Initialize Client ---
# This reads API keys and project settings from your .env file
# (LANGSMITH_API_KEY, LANGSMITH_PROJECT, etc.)
try:
    client = Client()
    logger.info("LangSmith Client initialized successfully.")
except Exception as e:
    logger.warning(f"Could not initialize LangSmith Client. Tracing will be disabled. Error: {e}")
#====================================

# #====================================
app = FastAPI(title="Process restaurant menu image and return vegetarian dishes and total price")
# #====================================

#====================================
# --- LANGSMITH: Step 3: Decorate the endpoint to create a "root trace" ---
@traceable(name="Process Menu Images Endpoint", run_type="chain")
@app.post("/process-images")
async def process_images(
    images: List[UploadFile] = File(...),
):
    # --- LANGSMITH: Step 4: Get the current run tree for logging ---
    # This 'root_run' object represents the entire trace for this request.
    try:
        root_run = get_current_run_tree()
        # This run_id *is* the request_id that links all services.
        trace_id = root_run.id
        logger.info(f"Starting trace with trace_id: {trace_id}")
    except Exception:
        # Fallback if tracing isn't configured
        root_run = None
        trace_id = "tracing_disabled"

    MAX_IMAGES = config["MAX_IMAGES"]
    warning_message: Optional[str] = None
    all_results = [] # --- LOGIC FIX: Collect all results, don't return in loop

    total_uploaded = len(images)
    
    # --- LANGSMITH: Step 5: Log inputs and metadata to the root trace ---
    if root_run:
        root_run.add_inputs({
            "image_count": total_uploaded,
            "filenames": [img.filename for img in images]
        })

    if total_uploaded > MAX_IMAGES:
        warning_message = f"Too many images uploaded ({total_uploaded}). Only the first {MAX_IMAGES} were processed."
        images = images[:MAX_IMAGES]
        # Log the warning
        if root_run:
            root_run.log(metadata={"warning": warning_message})

    for image in images:
        # --- LANGSMITH: Step 6: Create a nested span for each image processed ---
        # This groups all logic for one image under its own trace.
        with traceable(name="Process Single Image", run_type="chain") as image_run:
            image_run.add_inputs({
                "filename": image.filename,
                "content_type": image.content_type,
            })

            contents = await image.read()
            
            #--STEP 1 -> pass image to gemini and get all dishes with prices
            dish_prices_list = None
            # --- LANGSMITH: Step 7: Create a specific span for the OCR/Gemini call ---
            with traceable(name="Step 1: Extract Dishes (OCR/Gemini)") as ocr_run:
                try:
                    dish_prices_list = process_image_sync(contents)
                    # Log the raw output from this step
                    ocr_run.add_outputs({"extracted_dishes": dish_prices_list})
                    image_run.log(metadata={"step_1_raw_output": dish_prices_list})
                except Exception as e:
                    logger.error(f"Error in process_image_sync: {e}")
                    ocr_run.log(error=str(e))
                    image_run.log(error=f"Step 1 failed: {e}")
                    continue # Skip to the next image if OCR fails

            # --- NOTE: Removed the temp file logic for local testing ---
            # --- It adds noise to the trace. Re-add if essential.

            #--STEP 2 -> filter vegetarian dishes from results
            veg_dishes_prices_list = []
            if dish_prices_list:
                # --- LANGSMITH: Step 8: Create a span for the MCP tool call ---
                # This will automatically pass the trace_id in HTTP headers
                # if the MCP server is also configured for LangSmith tracing.
                with traceable(name="Step 2: Filter Veg Dishes (MCP)", run_type="tool") as mcp_run:
                    mcp_run.add_inputs({"dishes": [dish_prices_list]})
                    try:
                        async with streamablehttp_client(mcp_url) as (read, write, get_session_id):
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                mcp_run.log(metadata={"mcp_session": "initialized"})
                                
                                veg_dishes_prices_list = await session.call_tool("classify_sum_veg_prices", {"dishes": [dish_prices_list]})
                                veg_dishes_prices_list = veg_dishes_prices_list.content[0].text
                                
                                # Log the raw text before parsing
                                mcp_run.log(metadata={"raw_mcp_output": veg_dishes_prices_list})
                                
                                #--convert to json dict
                                veg_dishes_prices_list = json.loads(veg_dishes_prices_list)
                                
                                # Log the final parsed output of this step
                                mcp_run.add_outputs({"vegetarian_dishes": veg_dishes_prices_list})

                    except Exception as e:
                        logger.error(f"Error calling MCP tool: {e}")
                        mcp_run.log(error=str(e))
                        image_run.log(error=f"Step 2 failed: {e}")

            else:
                logger.debug(f"no dish_prices_list to filter vegetarian dishes")
                image_run.log(metadata={"info": "No dishes found in Step 1, skipping Step 2."})

            # --- LOGIC FIX: Add this image's result to the list ---
            all_results.append(veg_dishes_prices_list)
            image_run.add_outputs({"final_veg_dishes_for_image": veg_dishes_prices_list})

    # --- LANGSMITH: Step 9: Log the final aggregated output to the root trace ---
    if root_run:
        root_run.add_outputs({"all_processed_results": all_results})

    # --- LOGIC FIX: Return the complete list *after* the loop ---
    return all_results
            
# #==commands to run project
# # uvicorn main:app --reload --port 9000
# # python -m rag_modules.save_emb
# # python -m mcp_modules.server
# # if __name__ == "__main__":
# #     uvicorn.run(app, port=config["main_port"])