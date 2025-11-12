import os
import json
import argparse
import pathlib
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError("The 'GEMINI_API_KEY' environment variable is not set.")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-pro')

def get_dish_label(dish_name: str) -> str:
    """
    Classifies a dish as vegetarian or non-vegetarian using the Gemini API.

    Args:
        dish_name: Name of the dish as a string.

    Returns:
        "veg" or "non_veg"
    """

    prompt = f"""
    You are a strict vegetarian classification assistant.

    Classify the dish: "{dish_name}"

    Rules:
    - Return exactly one word: "veg" or "non_veg".
    - A dish is non_veg if it contains meat, chicken, mutton, fish, seafood, poultry, egg, or any non-vegetarian ingredient.
    - Dishes containing paneer, vegetables, cheese, mushrooms, grains, lentils, or milk products are veg.
    - Do not add explanations, no punctuation, no sentences, no symbols.

    Your response must be exactly one word:
    veg
    or
    non_veg
    """

    response = model.generate_content(prompt)
    label = response.text.strip().lower()

    # Safety: normalize unexpected outputs
    return "veg" if label.startswith("veg") else "non_veg"