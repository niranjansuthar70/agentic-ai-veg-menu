from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np
import os
import json
import argparse
import pathlib
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

emb_model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("knowledge_base.index")

with open("knowledge_base.json") as f:
    kb = json.load(f)

load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError("The 'GEMINI_API_KEY' environment variable is not set.")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

def get_gemini_label(dish_name: str) -> str:
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

    response = gemini_model.generate_content(prompt)
    label = response.text.strip().lower()

    # Safety: normalize unexpected outputs
    return "veg" if label.startswith("veg") else "non_veg"

def rag_lookup(dish_name, top_k=2):
    emb = emb_model.encode([dish_name])
    D, I = index.search(np.array(emb), top_k)
    results = [kb[i] for i in I[0]]
    return results

def classify_dish(dish_name):
    evidence = rag_lookup(dish_name)

    # Count veg vs non-veg hits (global retrieval signals)
    veg_score = sum(1 for e in evidence if e["veg"])
    nonveg_score = sum(1 for e in evidence if not e["veg"])

    print("veg_score:", veg_score)
    print("nonveg_score:", nonveg_score)
    print("evidence:", evidence)

    # ---- RULE 1: Direct match override (strongest signal) ----
    direct_match_nonveg = any(
        (not e["veg"]) and (dish_name.lower() in e["item"].lower())
        for e in evidence
    )

    if direct_match_nonveg:
        return {
            "is_vegetarian": False,
            "confidence": 1.0,
            "decision_reason": "Direct dish match indicates non-vegetarian.",
            "evidence": evidence
        }

    # ---- RULE 2: Majority Voting (semantic similarity support) ----
    if veg_score > nonveg_score + 1:
        # Strong veg majority
        return {
            "is_vegetarian": True,
            "confidence": 0.85,
            "decision_reason": "Strong majority evidence supports vegetarian.",
            "evidence": evidence
        }

    elif nonveg_score > veg_score + 1:
        # Strong non-veg majority
        return {
            "is_vegetarian": False,
            "confidence": 0.85,
            "decision_reason": "Strong majority evidence supports non-vegetarian.",
            "evidence": evidence
        }

    # ---- RULE 3: Ambiguous Case → fallback to LLM classification ----
    llm_label = get_gemini_label(dish_name)

    is_vegetarian = (llm_label == "veg")

    return {
        "is_vegetarian": is_vegetarian,
        "confidence": 0.4,
        "decision_reason": "Evidence ambiguous, fallback to LLM label.",
        "evidence": evidence
    }


#test the classifier
sample_data={"dishes": [{"name": "Chiken Curry", "price": "140"}, {"name": "Chiken Masala", "price": "150"}, {"name": "Boti", "price": "120"}, {"name": "Boti fry", "price": "130"}, {"name": "Chapati", "price": "15"}, {"name": "Paratha", "price": "20"}]}

sample_data_list=sample_data["dishes"]

for dish in sample_data_list:
    dish_name = dish["name"]
    print("dish_name: ", dish_name)
    result = classify_dish(dish_name)
    print("result: ", result)
    print("--------------------------------")