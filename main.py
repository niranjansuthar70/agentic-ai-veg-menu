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
#====================================

#====================================
app = FastAPI(title="Process restaurant menu image and return vegetarian dishes and total price")
#====================================

#====================================
@app.post("/process-images")
async def process_images(
    images: List[UploadFile] = File(...),
):
    MAX_IMAGES = config["MAX_IMAGES"]
    warning_message: Optional[str] = None
    image_details: List[Dict[str, Any]] = []
    total_price=None

    total_uploaded = len(images)

    if total_uploaded > MAX_IMAGES:
        warning_message = f"Too many images uploaded ({total_uploaded}). Only the first {MAX_IMAGES} were processed."
        images = images[:MAX_IMAGES]

    for image in images:
        contents = await image.read()
        
        # #--STEP 1 -> pass image to gemini and get all dishes with prices
        # dish_prices_list=process_image_sync(contents)
        # #--save to json in temp folder
        # #--check and create temp folder if not exists
        # if not os.path.exists('temp'):
        #     os.makedirs('temp')
        # with open('temp/dish_prices_list.json', 'w') as f:
        #     json.dump(dish_prices_list, f)
        # logger.debug(f"dish_prices_list: {dish_prices_list}")
        # logger.debug(f"type of dish_prices_list: {type(dish_prices_list)}")

        # ===for local testing -> no need to call gemini again and again
        with open('temp/dish_prices_list.json', 'r') as f:
            dish_prices_list = json.load(f)
            
        logger.debug(f"dish_prices_list: in main.py file: {dish_prices_list}")
        logger.debug(f"type of dish_prices_list: in main.py file {type(dish_prices_list)}")
        logger.debug(f"--------------------------------")

        #--STEP 2 -> filter vegetarian dishes from results
        if dish_prices_list:
            async with streamablehttp_client(mcp_url) as (read, write, get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()   
                    logger.debug("session initialized")
                    veg_dishes_prices_list = await session.call_tool("classify_sum_veg_prices", {"dishes": [dish_prices_list]})
                    logger.debug(f"veg_dishes_prices_list: {veg_dishes_prices_list} and type : {type(veg_dishes_prices_list)}")
                    # text = result.content[0].text
                    # print("Text:", text)
                    # #--convert to json dict
                    # total_price_dict = json.loads(text)
                    # print("total_price_dict: ", total_price_dict)
                    # print("type of total_price_dict: ", type(total_price_dict))
                    # total_price = total_price_dict.get("total_price", 0)
                    # print("total_price: ", total_price)
                    # print("type of total_price: ", type(total_price))
        else:
            logger.debug(f"no dish_prices_list to filter vegetarian dishes")
            vegetarian_dishes = {}

        # logger.debug("--------------------------------")
        # #--save vegetarian_dishes to json in temp folder
        # with open('temp/vegetarian_dishes.json', 'w') as f:
        #     json.dump(vegetarian_dishes, f)
        # logger.debug("vegetarian_dishes saved to temp/vegetarian_dishes.json")
        # logger.debug("--------------------------------")

#         # # #--check if temp/vegetarian_dishes.json exists
#         # with open('temp/vegetarian_dishes.json', 'r') as f:
#         #     vegetarian_dishes = json.load(f)
#         #--STEP 3 -> call MCP tool to calculate total price of vegetarian dishes
#         # #---call MCP tool to calculate total price of vegetarian dishes
#         print("vegetarian_dishes: ", vegetarian_dishes)
#         print("type of vegetarian_dishes: ", type(vegetarian_dishes))
#         print("--------------------------------")
#         if vegetarian_dishes:
#             async with streamablehttp_client(mcp_url) as (read, write, get_session_id):
#                 async with ClientSession(read, write) as session:
#                     await session.initialize()   
#                     print("session initialized")
#                     result = await session.call_tool("sum_veg_prices", {"dishes": vegetarian_dishes})
#                     print("result: ", result, "type: ", type(result))
#                     text = result.content[0].text
#                     print("Text:", text)
#                     #--convert to json dict
#                     total_price_dict = json.loads(text)
#                     print("total_price_dict: ", total_price_dict)
#                     print("type of total_price_dict: ", type(total_price_dict))
#                     total_price = total_price_dict.get("total_price", 0)
#                     print("total_price: ", total_price)
#                     print("type of total_price: ", type(total_price))

#         else:
#             print("no vegetarian dishes to calculate total price")
#             print("--------------------------------")
#             total_price = 0 

        
#         results={
#             "vegetarian_dishes": vegetarian_dishes,
#             "total_price": total_price
#         }
        
#         return results

# uvicorn main:app --reload --port 9000
# python -m rag_modules.save_emb
# python -m mcp_modules.server
# if __name__ == "__main__":
#     uvicorn.run(app, port=config["main_port"])