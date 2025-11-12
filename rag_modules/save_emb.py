from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np

#---load config file
from utils.load_config import load_config
#--import logger
from utils.logger_setup import get_logger
logger = get_logger(__name__)

#====================================
#--load config from config.yaml file
config = load_config()
#====================================
emb_model_id=config['emb_model']
emb_model = SentenceTransformer(emb_model_id)
logger.debug(f"embedding model :{emb_model_id} loaded successfully..")
#====================================

#====================================
json_path='rag_modules/' + config['knowledge_based_file_name'] + '.json'
with open(json_path) as f:
    data = json.load(f)
logger.debug(f"knowledge based json file : {json_path} loaded successfully..")
#====================================

#====================================
corpus = [d["item"] for d in data]
vectors = emb_model.encode(corpus)

index = faiss.IndexFlatL2(vectors.shape[1])
index.add(np.array(vectors))
#====================================

#====================================
index_file_path='rag_modules/' + config['knowledge_based_file_name'] + '.index'
faiss.write_index(index, index_file_path)
logger.debug(f"knowledge based index file : {index_file_path} created successfully..")
#====================================