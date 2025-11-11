from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# --- 1. Removed run_in_threadpool import ---
from typing import List, Optional, Dict, Any, Set
import io
from PIL import Image
from gemini_v0.gemini_extraction import extract_veg_dishes

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
            return {
                "vegetarian_dishes": None,
                "sum": None,
                "error": f"Error extracting vegetarian dishes with gemini: {e}"
            }

        return {
            # Use .get() for safety in case a function fails
            "vegetarian_dishes": image_menu_data.get("dishes"),
            "sum": image_menu_data.get("sum"),
            "error": None
        }
    except Exception as e:
        # Return the specific error
        return {
            "vegetarian_dishes": None,
            "sum": None,
            "error": f"Failed to process image: {str(e)}"
        }


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
        
        #--process image with gemini
        results=process_image_sync(contents)
        image_details.append({
            "filename": image.filename,
            **results
        })
        
        await image.close()

    return {
        "message": "Images processed",
        "processed_images": image_details,
        "warning": warning_message
    }