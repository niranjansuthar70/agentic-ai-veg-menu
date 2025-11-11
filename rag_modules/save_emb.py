from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
print("model loaded")

with open("knowledge_base.json") as f:
    data = json.load(f)
print("data loaded")

corpus = [d["item"] for d in data]
vectors = model.encode(corpus)

index = faiss.IndexFlatL2(vectors.shape[1])
index.add(np.array(vectors))

faiss.write_index(index, "knowledge_base.index")