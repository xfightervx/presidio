import json
import pickle
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt


with open("assets/k_means_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

headers = [entry["header"] for entry in data]
labels = [entry["label"] for entry in data]


model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(headers)


pca = PCA(n_components=20, random_state=42)
reduced_embeddings = pca.fit_transform(embeddings)


k = 4
kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
kmeans.fit(reduced_embeddings)


with open("models/kmeans_headers.pkl", "wb") as f:
    pickle.dump(kmeans, f)

with open("models/header_encoder.pkl", "wb") as f:
    pickle.dump(model, f)

with open("models/pca_transform.pkl", "wb") as f:
    pickle.dump(pca, f)


sil_score = silhouette_score(reduced_embeddings, kmeans.labels_)
print(f"🧪 Silhouette Score: {sil_score:.3f}")


pca_2d = PCA(n_components=2)
X_2d = pca_2d.fit_transform(embeddings)

plt.figure(figsize=(8, 6))
plt.scatter(X_2d[:, 0], X_2d[:, 1], c=kmeans.labels_, cmap='viridis', s=30)
plt.title("KMeans Clustering on Header Embeddings (2D PCA Projection)")
plt.xlabel("PC 1")
plt.ylabel("PC 2")
plt.grid(True)
plt.tight_layout()
plt.show()
