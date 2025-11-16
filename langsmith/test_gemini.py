import os
import google.generativeai as genai
from dotenv import load_dotenv
from langsmith import Client, traceable # --- 1. Import LangSmith 'traceable' ---

def setup_environment():
    """
    Loads environment variables from .env file and configures the Gemini API.
    """
    # Load variables from .env file into os.environ
    load_dotenv()
    
    # Configure the Gemini API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    
    # --- 2. Configure LangSmith (it reads from .env automatically) ---
    # Ensures LANGSMITH_API_KEY, LANGSMITH_PROJECT, etc., are set
    client = Client()
    print("LangSmith and Gemini clients configured.")


# --- 3. Use the '@traceable' decorator ---
# This tells LangSmith to "watch" this function.
@traceable(name="Gemini Prompt") # This 'name' will appear in your LangSmith UI
def run_gemini_prompt(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Generates content using the specified Gemini model.
    
    Args:
        prompt: The text prompt to send to the model.
        model_name: The name of the model to use.
    
    Returns:
        The generated text content.
    """
    try:
        # Note: Corrected the model name to a valid one as you noted.
        model = genai.GenerativeModel(model_name)
        
        # --- 4. This call is now being traced by LangSmith ---
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        print(f"Error generating content: {e}")
        return f"An error occurred: {e}"

def main():
    """
    Main function to set up the environment and run the prompt.
    """
    try:
        setup_environment()
        
        user_prompt = "Explain how AI works in a few words"
        
        print(f"Sending prompt: '{user_prompt}'")
        
        # Call the refactored, traceable function
        result = run_gemini_prompt(user_prompt)
        
        print("\n--- Gemini Response ---")
        print(result)
        print("\n-----------------------")
        print("Check your LangSmith project to see the trace!")
        
    except ValueError as ve:
        print(ve)

if __name__ == "__main__":
    main()