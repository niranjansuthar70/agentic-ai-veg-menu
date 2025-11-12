import os
import json
import argparse
import pathlib
from PIL import Image
from gemini_v0.load_gemini_model import load_gemini_model
from utils.logger_setup import get_logger

logger = get_logger(__name__)

logger.debug("loading gemini model in veg_dishes_filter.py")
gemini_model = load_gemini_model()
logger.debug("gemini model loaded in veg_dishes_filter.py")


def filter_veg_dishes(json_data: dict) -> dict:
    """
    Analyzes a JSON data containing the dishes using the Gemini API to extract vegetarian dishes.

    Args:
        json_data: The JSON data containing the dishes.

    Returns:
        A dictionary containing the filtered vegetarian dishes.
    """

    prompt = f"""
    You are an expert culinary assistant specializing in dietary restrictions.
    I will provide you with a JSON list of dishes from a restaurant menu. Your task is to analyze this list and identify only the dishes that are strictly vegetarian.

    A dish is vegetarian if it does not contain any meat, poultry, egg, omlett or fish. Assume dishes are vegetarian if their name and ingredients strongly suggest it (e.g., "Garden Salad", "Mushroom Risotto", "Cheese Pizza").
    Be cautious: a dish like "Chicken Caesar Salad" is NOT vegetarian.

    Return a new JSON object that contains only the vegetarian dishes from the list I provided.
    The JSON object must be in the exact same format as the input and adhere to the provided schema.
    Do not include any text, explanations, or markdown formatting before or after the JSON block.
    If no dishes are vegetarian, return an empty "dishes" array.
    
    Here is the JSON to analyze:
    {json.dumps(json_data['dishes'], indent=2)}
    """    

    # Generate content
    print("filtering vegetarian dishes... this may take a moment.")
    response = gemini_model.generate_content(prompt)

    # print('response: ', response)
    try:
        json_string = response.text.strip()
        # Remove markdown code block fences if they exist
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
        
        return json.loads(json_string)
    except (json.JSONDecodeError, AttributeError):
        print("Error: Failed to parse JSON from the model's response.")
        print("Raw response:", response.text)
        return {}

def main():
    """Main function to run the script from the command line."""
    json_file_path = 'temp/result.json'
    json_data = json.load(open(json_file_path))
    result_data = filter_veg_dishes(json_data)
    print('result_data: ', result_data)
    json_string = json.dumps(result_data, indent=2)
    #--save json to temp folder
    #--check and create temp folder if not exists
    if not os.path.exists('temp'):
        os.makedirs('temp')
    with open('temp/filtered_result.json', 'w') as f:
        f.write(json_string)    
    print("JSON saved to temp/filtered_result.json")

if __name__ == "__main__":
    main()