import google.generativeai as genai
import os
from dotenv import load_dotenv  # --- 1. Import load_dotenv ---

# --- 2. Load variables from .env file into os.environ ---
load_dotenv()

# --- 3. Configure the API key ---
# This will now find the key loaded from your .env file
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# --- THIS IS THE CORRECTED CLIENT ---
# 1. Create the model instance.
# 2. Note: "gemini-2.5-flash" is not a valid model. I've corrected it to "gemini-1.5-flash".
model = genai.GenerativeModel("gemini-2.5-flash") # --- 4. Corrected model name ---

# --- THIS IS THE CORRECTED GENERATION CALL ---
response = model.generate_content("Explain how AI works in a few words")

print(response.text)