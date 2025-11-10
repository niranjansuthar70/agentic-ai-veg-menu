import os
import json
import argparse
import pathlib
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def extract_veg_dishes(img: Image.Image) -> dict:
    """
    Analyzes a menu image using the Gemini API to extract vegetarian dishes.

    Args:
        image_path: The file path to the menu image.

    Returns:
        A dictionary containing the extracted vegetarian dishes.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError("The 'GEMINI_API_KEY' environment variable is not set.")

    # Configure the Gemini API client
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    # Set up the model and prompt
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = """
    Analyze the provided restaurant menu image. Your task is to extract ONLY the vegetarian dishes and their corresponding prices.

    Return the output as a single, valid JSON object. Do not include any text or markdown formatting before or after the JSON block.

    The JSON object should have a single top-level key: "vegetarian_dishes".
    The value of "vegetarian_dishes" should be an array of objects.
    Each object in the array should represent a vegetarian dish and have the following two keys:
    1. "name": The name of the dish (string).
    2. "price": The price of the dish (string).
    3. "sum": at the end of the array, sum of the prices all vegetarian dishes

    - If a dish is explicitly vegetarian (e.g., "Veg Pulao"), include it.
    - If an item is a vegetarian component within a non-vegetarian meal (like "Veg Rayta Special" in a "Chicken Thali"), list it. For its price, you can state "Part of Thali".
    - Do not include any non-vegetarian items like chicken, mutton, or egg dishes.
    - If there are no vegetarian dishes at all, return an empty array for the "vegetarian_dishes" key.
    """

    # Generate content
    print("AI is analyzing the menu... this may take a moment.")
    response = model.generate_content([prompt, img])
    
    # Clean and parse the JSON response
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
        raise ValueError("Could not get a valid JSON response from the AI model.")


def main():
    """Main function to run the script from the command line."""
    parser = argparse.ArgumentParser(
        description="Extract vegetarian dishes and prices from a menu image using AI."
    )
    parser.add_argument(
        "image_path",
        type=pathlib.Path,
        help="The path to the menu image file (e.g., menu.jpg)."
    )
    args = parser.parse_args()

    try:
        img = Image.open(args.image_path)
        result_data = extract_veg_dishes(img)
        print("\n--- Extracted Vegetarian Dishes ---")
        print(json.dumps(result_data, indent=2))
        print("---------------------------------")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()

# python main.py ././menu1.PNG