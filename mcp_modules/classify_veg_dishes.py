from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np
import os
import json
import argparse
import pathlib
from PIL import Image
from typing import Any
# from gemini_v0.load_gemini_model import load_gemini_model
from model_instances import gemini_model_instance


#---load config file
from utils.load_config import load_config
#--import logger
from utils.logger_setup import get_logger

# --- LANGSMITH: Step 1: Import tracing components ---
from langsmith import traceable
# from langsmith.run_trees import add_metadata # <-- CORRECT

logger = get_logger(__name__)

logger.debug("calling gemini model in classify_veg_dishes.py")
gemini_model = gemini_model_instance
logger.debug("gemini model called in classify_veg_dishes.py")
#====================================
#--load config from config.yaml file
config = load_config()
#====================================
emb_model_id=config['emb_model']
emb_model = SentenceTransformer(emb_model_id)
logger.debug(f"embedding model :{emb_model_id} loaded successfully..")
#====================================
#--loading embedding model
index_file_path='rag_modules/' + config['knowledge_based_file_name'] + '.index'
index = faiss.read_index(index_file_path)

json_path='rag_modules/' + config['knowledge_based_file_name'] + '.json'
with open(json_path) as f:
    kb = json.load(f)

#====================================
# --- LANGSMITH: Step 2: Trace the RAG retriever ---
@traceable(name="RAG Lookup", run_type="retriever")
def rag_lookup(dish_name, top_k=2):
    emb = emb_model.encode([dish_name])
    D, I = index.search(np.array(emb), top_k)
    results = [kb[i] for i in I[0]]
    # The return value 'results' will be automatically logged as the
    # 'documents' output of this retriever step.
    return results
#====================================

#====================================
# --- LANGSMITH: Step 3: Trace the fallback LLM call ---
@traceable(name="Gemini Classifier", run_type="llm")
def get_gemini_label(dish_name: str) -> str:
    """
    Classifies a dish as vegetarian or non-vegetarian using the Gemini API.

    Args:
        dish_name: Name of the dish as a string.

    Returns:
        "veg" or "non_veg"
    """

    # --- LANGSMITH: Add model metadata for cost/token tracking ---
    # try:
    #     add_metadata({"model_name": gemini_model.model_name})
    # except Exception as e:
    #     logger.warning(f"Could not log LangSmith metadata: {e}")

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
#====================================

#====================================
# --- LANGSMITH: Step 4: Trace the core business logic ---
@traceable(name="Classify Single Dish")
def classify_single_dish(dish_name):
    # This will now appear as a nested 'RAG Lookup' span
    evidence = rag_lookup(dish_name)

    # Count veg vs non-veg hits (global retrieval signals)
    veg_score = sum(1 for e in evidence if e["veg"])
    nonveg_score = sum(1 for e in evidence if not e["veg"])

    logger.debug(f"veg_score :{veg_score}")
    logger.debug(f"nonveg_score :{nonveg_score}")
    logger.debug(f"evidence :{evidence}")
    
    # (Note: You could use 'run.log(metadata=...)' here to log scores,
    # but the full return value is logged automatically anyway)

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
    
    # This will now create a nested 'Gemini Classifier' LLM span
    # *only* when this fallback rule is triggered.
    llm_label = get_gemini_label(dish_name)

    is_vegetarian = (llm_label == "veg")

    return {
        "is_vegetarian": is_vegetarian,
        "confidence": 0.4,
        "decision_reason": "Evidence ambiguous, fallback to LLM label.",
        "evidence": evidence
    }

# --- LANGSMITH: Step 5: Trace the main entrypoint function ---
@traceable(name="Classify All Dishes")
def classify_dishes(dishes: list[dict[str, Any]]) -> dict[str, Any]:
    logger.debug(f'reached inside -> classify_dishes')
    classification_result=[]

    for dish in dishes[0]['dishes']:
        dish_name=dish['name']
        dish_price = float(dish.get('price', 0) or 0)
        logger.debug(f'checking for dish : {dish_name}')
        
        # This will now create a new 'Classify Single Dish' span
        # for every single dish in the loop.
        dish_classify_result=classify_single_dish(dish_name=dish_name)
        logger.debug(f'dish_classify_result: {dish_classify_result}')

        #--process only if vegetarin dish found
        if dish_classify_result['is_vegetarian']:
            logger.debug(f'veg dish found...appending to classification_result')
            dish_classify_result['dish_name']=dish_name
            dish_classify_result['dish_price']=dish_price
            classification_result.append(dish_classify_result)

    return classification_result