from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional, Dict, Any, Set
import os
import json
from dotenv import load_dotenv
from utils.helper_functions import process_image_sync, filter_vegetarian_dishes
import shutil
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import json
import asyncio

#====================================
#--load mcp_url from .env file
load_dotenv()
mcp_url = os.getenv("mcp_url")
print("mcp_url: ", mcp_url)
local_testing = os.getenv("local_testing")
print("local_testing: ", local_testing)
#====================================

#====================================
app = FastAPI(title="Process images and return dimensions")
#====================================

#====================================
@app.post("/process-images")
async def process_images(
    images: List[UploadFile] = File(...),
):
    MAX_IMAGES = 5
    warning_message: Optional[str] = None
    image_details: List[Dict[str, Any]] = []
    total_price=None

    total_uploaded = len(images)

    if total_uploaded > MAX_IMAGES:
        warning_message = f"Too many images uploaded ({total_uploaded}). Only the first {MAX_IMAGES} were processed."
        images = images[:MAX_IMAGES]

    for image in images:
        contents = await image.read()
        
        #--STEP 1 -> pass image to gemini and get all dishes with prices
        results=process_image_sync(contents)
        #--save to json in temp folder
        #--check and create temp folder if not exists
        if not os.path.exists('temp'):
            os.makedirs('temp')
        with open('temp/results.json', 'w') as f:
            json.dump(results, f)
        print("results: ", results)
        print("type of results: ", type(results))

        #===for local testing -> no need to call gemini again and again
        # with open('temp/results.json', 'r') as f:
        #     results = json.load(f)
            
        # print("results: in main.py file ", results)
        # print("type of results: in main.py file ", type(results))
        # print("--------------------------------")

        #--STEP 2 -> filter vegetarian dishes from results
        if results:
            vegetarian_dishes = filter_vegetarian_dishes(results)
        else:
            print("no results to filter vegetarian dishes")
            vegetarian_dishes = {}

        print("--------------------------------")
        #--save vegetarian_dishes to json in temp folder
        with open('temp/vegetarian_dishes.json', 'w') as f:
            json.dump(vegetarian_dishes, f)
        print("vegetarian_dishes saved to temp/vegetarian_dishes.json")
        print("--------------------------------")

        # # #--check if temp/vegetarian_dishes.json exists
        # with open('temp/vegetarian_dishes.json', 'r') as f:
        #     vegetarian_dishes = json.load(f)
        #--STEP 3 -> call MCP tool to calculate total price of vegetarian dishes
        # #---call MCP tool to calculate total price of vegetarian dishes
        print("vegetarian_dishes: ", vegetarian_dishes)
        print("type of vegetarian_dishes: ", type(vegetarian_dishes))
        print("--------------------------------")
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

        else:
            print("no vegetarian dishes to calculate total price")
            print("--------------------------------")
            total_price = 0 

        
        results={
            "vegetarian_dishes": vegetarian_dishes,
            "total_price": total_price
        }
        
        return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

# uvicorn main:app --reload --port 9000
