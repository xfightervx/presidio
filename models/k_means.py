import json
import pickle
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer

with open("assets/k_means_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

headers = [entry["header"] for entry in data]
labels = [entry["label"] for entry in data]  


model = SentenceTransformer("all-MiniLM-L6-v2")


embeddings = model.encode(headers)

k = 4
kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
kmeans.fit(embeddings)


with open("models/kmeans_headers.pkl", "wb") as f:
    pickle.dump(kmeans, f)

with open("models/header_encoder.pkl", "wb") as f:
    pickle.dump(model, f)
