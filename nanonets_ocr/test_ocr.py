from docstrange import DocumentExtractor
import json
import os
from model_instances import gemini_model_instance
from utils.logger_setup import get_logger

logger = get_logger(__name__)

logger.debug("calling gemini model in test_ocr.py")
gemini_model = gemini_model_instance
logger.debug("gemini model called in test_ocr.py")

def extract_dishes_from_text(menu_text: str) -> dict:
    """
    Analyzes menu text (CSV format) using the Gemini API to extract dishes 
    into a structured JSON format with variable pricing logic.

    Args:
        menu_text: The string containing CSV data extracted from the image.

    Returns:
        A dictionary containing the extracted dishes in structured JSON.
    """

    prompt = f"""
    You are a data parsing assistant. Analyze the provided restaurant menu data, which is in CSV/Text format. 
    Your task is to convert this data into a structured JSON object.

    Input Data:
    {menu_text}

    **Rules for Extraction:**
    1. **Categories:** Group items into `menu_categories` based on the headers found in the text (e.g., "Non-Veg Dishes", "Chinese Non-Veg").
    2. **Pricing Logic:**
       - **Variable Pricing:** If a price column contains multiple values (e.g., "120/- 225/- 450/-") or headers indicate sizes (Quarter/Half/Full), set `pricing_type` to "variable" and map the prices to keys like "quarter", "half", "full".
       - **Fixed Pricing:** If there is only one price, set `pricing_type` to "fixed" and map it to "standard" or "full" (if explicitly stated).
       - Remove currency symbols (Rs, /-) and convert numbers to integers. Assign 0 if no price is listed.
    3. **Thalis:** If the item contains a list of included items (like a description), include that in the details.

    **Required JSON Output Structure:**
    Return ONLY valid JSON. Use this exact schema:
    {{
      "menu_categories": [
        {{
          "category": "Category Name",
          "items": [
            {{
              "dish_name": "Dish Name",
              "pricing_type": "variable", 
              "prices": {{ "quarter": 120, "half": 220, "full": 400 }} 
            }},
            {{
              "dish_name": "Single Price Dish",
              "pricing_type": "fixed", 
              "prices": {{ "standard": 150 }} 
            }}
          ]
        }}
      ]
    }}
    """

    logger.debug("AI is analyzing the CSV text to generate JSON structure...")
    
    # --- LANGSMITH: Step 4: This call is now traced ---
    # Note: We are passing the prompt string only, as the CSV is embedded in the prompt
    response = gemini_model.generate_content(prompt)

    #---clean and parse the JSON response
    try:
        json_string = response.text.strip()
        #---remove markdown code block fences if they exist
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
        
        parsed_json = json.loads(json_string)
        return parsed_json
        
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Error: Failed to parse JSON from the model's response. {e}")
        logger.debug(f"Raw response: {response.text}")
        return {}

def main():
    image_path = "nanonets_ocr/menu1.PNG"

    if not os.path.exists(image_path):
        logger.error(f"File not found: {image_path}")
        return

    # 1. Extract Text/CSV using DocStrange
    logger.info(f"Extracting text from {image_path} using DocStrange...")
    extractor = DocumentExtractor()
    image_result = extractor.extract(image_path)
    
    # Extract CSV text from OCR
    csv_output = image_result.extract_csv()
    logger.info("CSV Text extracted successfully.")
    logger.debug(f"Extracted CSV Content:\n{csv_output}")

    # 2. Pass Extracted Text to LLM for JSON Structuring
    if csv_output and len(csv_output.strip()) > 0:
        final_json = extract_dishes_from_text(csv_output)
        
        # Print the result
        print(json.dumps(final_json, indent=2))
        
        # Optional: Save to file
        with open("menu_output.json", "w") as f:
            json.dump(final_json, f, indent=2)
            logger.info("JSON saved to menu_output.json")
    else:
        logger.warning("DocStrange extraction returned empty text. Skipping LLM step.")

if __name__ == "__main__":
    main()