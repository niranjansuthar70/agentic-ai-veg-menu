import os
import json
import argparse
import pathlib
from PIL import Image

# from gemini_v0.load_gemini_model import load_gemini_model
from model_instances import gemini_model_instance
from utils.logger_setup import get_logger

# --- LANGSMITH: Step 1: Import tracing components ---
from langsmith import traceable
# from langsmith.run_trees import add_metadata # <-- CORRECT

logger = get_logger(__name__)

logger.debug("calling gemini model in gemini_extraction.py")
gemini_model = gemini_model_instance
logger.debug("gemini model called in gemini_extraction.py")

# --- LANGSMITH: Step 2: Add the decorator ---
# This tells LangSmith to trace this function as an "llm" call,
# which automatically tracks inputs, outputs, tokens, and latency.
@traceable(name="Gemini Vision Extraction", run_type="llm")
def extract_dishes_with_prices(img: Image.Image) -> dict:
    """
    Analyzes a menu image using the Gemini API to extract dishes with prices.

    Args:
        image_path: The file path to the menu image.

    Returns:
        A dictionary containing the extracted dishes with prices.
    """

    prompt = """
    Analyze the provided restaurant menu image. Your task is to extract the dishes and their corresponding prices.

    Return the output as a single, valid JSON object. Do not include any text or markdown formatting before or after the JSON block.

    The JSON object should have a single top-level key: "dishes".
    The value of "dishes" should be an array of objects.
    Each object in the array should represent a dish and have the following two keys:
    1. "name": The name of the dish (string).
    2. "price": The price of the dish (string).
    """

    # --- LANGSMITH: Step 3: (Optional but recommended) Add model metadata ---
    # This helps LangSmith correctly identify the model for cost tracking.
    # We access the 'model_name' attribute from the GenerativeModel instance.
    # try:
    #     add_metadata({"model_name": gemini_model.model_name})
    # except Exception as e:
    #     logger.warning(f"Could not log LangSmith metadata: {e}")

    # Generate content
    logger.debug("AI is analyzing the menu to extract dishes and their prices... this may take a moment.")
    
    # --- LANGSMITH: Step 4: This call is now traced ---
    response = gemini_model.generate_content([prompt, img])

    #---clean and parse the JSON response
    try:
        json_string = response.text.strip()
        #---remove markdown code block fences if they exist
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
        
        parsed_json = json.loads(json_string)
        
        # The 'response' object is automatically logged as the output,
        # but you could also explicitly log the parsed JSON.
        # This function's return value is logged as the final output.
        return parsed_json
        
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Error: Failed to parse JSON from the model's response.")
        logger.debug(f"Raw response: {response.text}")
        # Return an empty dict on failure
        return {}


# (The main function remains unchanged, it will work as before)
# def main():
#     """Main function to run the script from the command line."""
#     parser = argparse.ArgumentParser(
#         description="Extract vegetarian dishes and prices from a menu image using AI."
#     )
#     parser.add_argument(
#         "image_path",
#         type=pathlib.Path,
#         help="The path to the menu image file (e.g., menu.jpg)."
#     )
#     args = parser.parse_args()

#     try:
#         img = Image.open(args.image_path)
#         result_data = extract_dishes_with_prices(img)
#         json_string = json.dumps(result_data, indent=2)
#         #--save json to temp folder
#         #--check and create temp folder if not exists
#         if not os.path.exists('temp'):
#             os.makedirs('temp')
#         with open('temp/result.json', 'w') as f:
#             f.write(json_string)    
#         print("JSON saved to temp/result.json")
#     except Exception as e:
#         print(f"An error occurred: {e}")

# if __name__ == "__main__":
#     main()