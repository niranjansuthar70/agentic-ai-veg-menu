from PIL import Image
import io
from typing import Dict, Any
from gemini_v0.gemini_extraction import extract_dishes_with_prices
from utils.logger_setup import get_logger

logger = get_logger(__name__)

def process_image_sync(contents: bytes) -> Dict[str, Any]:
    try:
        pil_image = Image.open(io.BytesIO(contents))
        image_menu_data: Dict[str, Any] = {}

        try:
            logger.debug("Extracting dishes with prices from image using Gemini...")
            image_menu_data = extract_dishes_with_prices(pil_image)
        except Exception as e:
            logger.warning(f"Error extracting dishes with prices: {e}", exc_info=True)
            return {}

        return image_menu_data
    except Exception as e:
        logger.warning(f"Error processing image: {e}", exc_info=True)
        return {}