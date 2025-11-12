#--load gemini model from config.yaml file
import google.generativeai as genai
from utils.load_config import load_config
import os
from dotenv import load_dotenv

#---load .env file
load_dotenv()

#---load config from config.yaml file
config = load_config()
gemini_model = config["gemini_model_id"]
print("gemini_model: ", gemini_model)


def load_gemini_model():
    #---check if GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError("The 'GEMINI_API_KEY' environment variable is not set.")

    #---configure the Gemini API client
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    #---set up the model and prompt
    model = genai.GenerativeModel(gemini_model)

    #============================================

    return model