from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# --- 1. Removed run_in_threadpool import ---
from typing import List, Optional, Dict, Any, Set
import io
from PIL import Image
from gemini_v0.gemini_extraction import extract_veg_dishes
from gemini_v0.veg_dishes_filter import filter_veg_dishes
import os
import json
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

mcp_url = "http://127.0.0.1:8000/mcp"

app = FastAPI(title="Process images and return dimensions")

def process_image_sync(contents: bytes) -> Dict[str, Any]:
    """
    This SYNCHRONOUS function now contains the conditional logic
    based on the 'method' argument.
    """
    try:
        pil_image = Image.open(io.BytesIO(contents))
        
        image_menu_data: Dict[str, Any] = {}

        try:
            print('extracting vegetarian dishes with gemini')
            # This is assumed to be a blocking call
            image_menu_data = extract_veg_dishes(pil_image)
        except Exception as e:
            print(f"Error extracting vegetarian dishes with gemini: {e}")
            return {}

        return image_menu_data
    except Exception as e:
        # Return the specific error
        return {}

def filter_vegetarian_dishes(results: dict) -> dict:
    """
    Filter vegetarian dishes from the results.
    """
    if results:
        vegetarian_dishes = filter_veg_dishes(results)
        return vegetarian_dishes
    return {}


@app.post("/process-images")
async def process_images(
    # Your file list remains the same
    images: List[UploadFile] = File(...),
):
    MAX_IMAGES = 5
    warning_message: Optional[str] = None
    image_details: List[Dict[str, Any]] = []

    total_uploaded = len(images)

    if total_uploaded > MAX_IMAGES:
        warning_message = f"Too many images uploaded ({total_uploaded}). Only the first {MAX_IMAGES} were processed."
        images = images[:MAX_IMAGES]

    for image in images:
        contents = await image.read()
        
        # #--process image with gemini
        # results=process_image_sync(contents)
        # #--save to json in temp folder
        # #--check and create temp folder if not exists
        # if not os.path.exists('temp'):
        #     os.makedirs('temp')
        # with open('temp/results.json', 'w') as f:
        #     json.dump(results, f)
        # print("results: ", results)
        # print("type of results: ", type(results))

        # #---check if temp/results.json exists
        # if os.path.exists('temp/results.json'):
        #     print("temp/results.json exists")
        #     with open('temp/results.json', 'r') as f:
        #         results = json.load(f)
            
        # else:
        #     print("temp/results.json does not exist")
        #     results = {}
        
        # print("results: ", results)
        # print("type of results: ", type(results))
        
        # #--process initial json data to filter vegetarian dishes
        # if results:
        #     vegetarian_dishes = filter_vegetarian_dishes(results)
        #     print("vegetarian_dishes: ", vegetarian_dishes)
        #     print("type of vegetarian_dishes: ", type(vegetarian_dishes))
        # else:
        #     print("no results to filter vegetarian dishes")
        #     vegetarian_dishes = {}

        # #--save vegetarian_dishes to json in temp folder
        # #--check and create temp folder if not exists
        # if not os.path.exists('temp'):
        #     os.makedirs('temp')
        # with open('temp/vegetarian_dishes.json', 'w') as f:
        #     json.dump(vegetarian_dishes, f)
        # print("vegetarian_dishes saved to temp/vegetarian_dishes.json")

        #---call MCP tool to calculate total price of vegetarian dishes
        #--check if temp/vegetarian_dishes.json exists
        if os.path.exists('temp/vegetarian_dishes.json'):
            with open('temp/vegetarian_dishes.json', 'r') as f:
                vegetarian_dishes = json.load(f)
            print("vegetarian_dishes: ", vegetarian_dishes)
            print("type of vegetarian_dishes: ", type(vegetarian_dishes))
        else:
            print("temp/vegetarian_dishes.json does not exist")
            vegetarian_dishes = {}

        #--call MCP tool to calculate total price of vegetarian dishes
        if vegetarian_dishes:
            async with streamablehttp_client(mcp_url) as (read, write, get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()   
                    print("session initialized")
                    result = await session.call_tool("sum_veg_prices", {"dishes": vegetarian_dishes})
                    print("result: ", result, "type: ", type(result))
                    text = result.content[0].text
                    print("Text:", text)
                    #--convert to json dict
                    total_price_dict = json.loads(text)
                    print("total_price_dict: ", total_price_dict)
                    print("type of total_price_dict: ", type(total_price_dict))
                    total_price = total_price_dict.get("total_price", 0)
                    print("total_price: ", total_price)
                    print("type of total_price: ", type(total_price))
        
        results   ={
            "vegetarian_dishes": vegetarian_dishes,
            "total_price": total_price
        }
        return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)