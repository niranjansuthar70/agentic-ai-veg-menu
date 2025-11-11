from PIL import Image
import io
from typing import Dict, Any
from gemini_v0.gemini_extraction import extract_veg_dishes
from gemini_v0.veg_dishes_filter import filter_veg_dishes



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
        print(f"Error processing image: {e}")
        return {}

def filter_vegetarian_dishes(results: dict) -> dict:
    """
    Filter vegetarian dishes from the results.
    """
    if results:
        return filter_veg_dishes(results)
    return {}