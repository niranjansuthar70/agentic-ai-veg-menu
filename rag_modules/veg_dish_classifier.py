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
    # print("emb: ", emb)
    D, I = index.search(np.array(emb), top_k)
    # print("D: ", D)
    # print("I: ", I)
    results = [kb[i] for i in I[0]]
    return results

def classify_dish(dish_name):
    evidence = rag_lookup(dish_name)

    # Count veg vs non-veg hits (global retrieval signals, not direct match signals)
    veg_score = sum(1 for e in evidence if e["veg"])
    nonveg_score = sum(1 for e in evidence if not e["veg"])

    print("veg_score: ", veg_score)
    print("nonveg_score: ", nonveg_score)
    print("evidence: ", evidence)

    # ---- RULE 1: Direct match override (strongest signal) ----
    direct_match_nonveg = any(
        (not e["veg"]) and (dish_name.lower() in e["item"].lower())
        for e in evidence
    )

    if direct_match_nonveg:
        is_vegetarian = False
        confidence = 1.0

    # ---- RULE 2: Scoring fallback (semantic / similarity support) ----
    elif veg_score + nonveg_score > 0:  # ensures no divide-by-zero
        is_vegetarian = veg_score > nonveg_score
        confidence = max(0.3, min(1.0, veg_score / (veg_score + nonveg_score)))

    # ---- RULE 3: Final fallback → LLM Label (weakest / expensive call) ----
    else:
        llm_label = get_gemini_label(dish_name)
        print("llm_label: ", llm_label)

        is_vegetarian = True if llm_label == "veg" else False
        confidence = 0.4

    #--return only vegetarian dishes
    if is_vegetarian:
        return {
            "dish_name": dish_name,
            "is_vegetarian": is_vegetarian,
            "confidence": round(confidence, 2),
            "evidence": evidence[:3]  # include reasoning notes
        }
    else:
        return None


#test the classifier
sample_data={"dishes": [{"name": "Chiken Curry", "price": "140"}, {"name": "Chiken Masala", "price": "150"}, {"name": "Boti", "price": "120"}, {"name": "Boti fry", "price": "130"}, {"name": "Chapati", "price": "15"}, {"name": "Paratha", "price": "20"}]}

sample_data_list=sample_data["dishes"]

for dish in sample_data_list:
    dish_name = dish["name"]
    print("dish_name: ", dish_name)
    result = classify_dish(dish_name)
    print("result: ", result)
    print("--------------------------------")