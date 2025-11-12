# model_instances.py
import os
from threading import Lock
from dotenv import load_dotenv
import google.generativeai as genai
from utils.load_config import load_config
from utils.logger_setup import get_logger

# --- Initialize logger ---
logger = get_logger(__name__)

# --- Load environment and config ---
load_dotenv()
config = load_config()

class ModelInstances:
    """
    Singleton-style class to manage AI model instances.
    Ensures that each model is loaded only once across the entire app.
    """

    _gemini_model = None
    _lock = Lock()

    @staticmethod
    def get_gemini_model():
        """
        Loads and returns a singleton instance of the Gemini model.
        Reads model ID from config.yaml and uses GEMINI_API_KEY from environment.
        """
        if ModelInstances._gemini_model is None:
            with ModelInstances._lock:
                if ModelInstances._gemini_model is None:
                    logger.debug("Loading Gemini model for the first time...")

                    # --- Validate API key ---
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key:
                        raise EnvironmentError("The 'GEMINI_API_KEY' environment variable is not set.")

                    # --- Configure Gemini client ---
                    genai.configure(api_key=api_key)

                    # --- Load model ID from config ---
                    gemini_model_id = config["gemini_model_id"]
                    logger.debug(f"Using Gemini model ID: {gemini_model_id}")

                    # --- Create model instance ---
                    ModelInstances._gemini_model = genai.GenerativeModel(gemini_model_id)
                    logger.debug("Gemini model loaded successfully.")
        else:
            logger.debug("Reusing already loaded Gemini model instance.")

        return ModelInstances._gemini_model


# === Load Gemini model at import time ===
logger.debug("Initializing and caching Gemini model instance...")
gemini_model_instance = ModelInstances.get_gemini_model()
logger.debug("Gemini model is ready for reuse.")