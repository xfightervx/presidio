import pickle
from sklearn.metrics import homogeneity_score, completeness_score, v_measure_score
from sklearn.preprocessing import LabelEncoder

# Test dataset
test_data = [
    {"header": "birth_date", "label": "Temporal"},
    {"header": "signup_date", "label": "Temporal"},
    {"header": "amount_due", "label": "Other"},
    {"header": "credit_limit", "label": "Other"},
    {"header": "gender", "label": "PII"},
    {"header": "full_name", "label": "PII"},
    {"header": "zip_code", "label": "Geographic"},
    {"header": "city", "label": "Geographic"},
    {"header": "email", "label": "PII"},
    {"header": "salary", "label": "Other"},
    {"header": "payment_date", "label": "Temporal"},
    {"header": "country", "label": "Geographic"},
    {"header": "last_name", "label": "PII"},
    {"header": "account_balance", "label": "Other"},
    {"header": "state", "label": "Geographic"},
    {"header": "phone", "label": "PII"},
    {"header": "transaction_date", "label": "Temporal"},
    {"header": "postal_code", "label": "Geographic"},
    {"header": "annual_income", "label": "Other"},
    {"header": "user_id", "label": "PII"},
]

headers = [entry["header"] for entry in test_data]
true_labels = [entry["label"] for entry in test_data]


with open("models/kmeans_headers.pkl", "rb") as f:
    kmeans = pickle.load(f)

with open("models/header_encoder.pkl", "rb") as f:
    encoder = pickle.load(f)

with open("models/pca_transform.pkl", "rb") as f:
    pca = pickle.load(f)


embeddings = encoder.encode(headers)
reduced_embeddings = pca.transform(embeddings)


predicted_clusters = kmeans.predict(reduced_embeddings)


le = LabelEncoder()
true_label_ids = le.fit_transform(true_labels)


homogeneity = homogeneity_score(true_label_ids, predicted_clusters)
completeness = completeness_score(true_label_ids, predicted_clusters)
v_measure = v_measure_score(true_label_ids, predicted_clusters)

print(f"Homogeneity Score:  {homogeneity:.3f}")
print(f"Completeness Score: {completeness:.3f}")
print(f"V-Measure Score:    {v_measure:.3f}")
