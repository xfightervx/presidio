# 📦 Smart Auto-Tagging for PII Detection and Masking

This project aims to build a **smart auto-tagging and anonymization engine** for detecting and masking **Personally Identifiable Information (PII)** in CSV files. It includes custom recognizers, semantic profiling, scoring based on headers, and a minimal frontend for report visualization.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/xfightervx/presidio.git
cd presidio
```

### 2. Setup Python Environment

#### ✅ With `uv` (recommended)

```bash
uv init
echo "3.12" > .python-version
uv venv
source .venv/Scripts/activate  # (Linux: source .venv/bin/activate)
uv pip install -r requirements.txt
```

If you encounter an error with `thinc`, run:

```bash
uv pip install --upgrade --force-reinstall numpy thinc spacy
```

#### ✅ With `pip` (Python 3.10–3.12 required)

```bash
python -m venv .venv
source .venv/Scripts/activate  # (Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

---

## 🧠 Extending with Custom Entities

To add new entities to the analyzer:

1. Create a new recognizer (class or pattern) in `core/logic/`.
2. Register it in the `get_analyzer()` function at the end of `core/logic.py`.

---

## 🧪 Testing

### 1. Unit Testing

Add your test function to `tests/test_entities/` and use the helper `assert_recognition`.

Run tests with:

```bash
python -m unittest discover tests/
```

### 2. Evaluation Suite

You can also add test cases to `assets/test_dataset.json` and run:

```bash
python evaluate_recognizers.py
```

This generates a detailed precision/recall report for each entity.

---

## 📂 Running the CSV Masking

To analyze and mask a CSV file:

```python
from core.csv_pii import process_csv
import json

masked_df, masking_report = process_csv("assets/test.csv")

masked_df.to_csv("assets/masked_test.csv", index=False)

with open("assets/masking_report.json", "w") as f:
    json.dump(masking_report, f, indent=2)
```

---

## 🖼️ Frontend Report Viewer

A minimal app to upload the csv files and get fullon recommnedations.

1. Put the masking report data into `gdpr-dashboard/src/data/`
2. Install frontend dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

## 🖼️ Backend

the back end is also minimal just

```bash
unicorn core.backend:app
```

ENJOY.