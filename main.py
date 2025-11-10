from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# --- 1. Removed run_in_threadpool import ---
from typing import List, Optional, Dict, Any, Set
import io
from PIL import Image

app = FastAPI(title="Process images and return dimensions")

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
        
        #--read and show image width and height
        pil_image = Image.open(io.BytesIO(contents))
        width, height = pil_image.size
        image_details.append({
            "filename": image.filename,
            "width": width,
            "height": height,
        })
        
        await image.close()

    return {
        "message": "Images processed",
        "processed_images": image_details,
        "warning": warning_message
    }