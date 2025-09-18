# 📦 Smart Auto-Tagging for PII Detection and Masking

This project builds a **smart auto-tagging and anonymization engine** for detecting and masking **Personally Identifiable Information (PII)** in CSV files. It includes custom recognizers, semantic profiling, scoring based on headers, and a minimal frontend for report visualization.

---

## ⚡ Quickstart (recommended)

> One command installs **uv**, sets up the Python env, creates your **.env** from the template, and (optionally) builds the local **Ollama** model from the **Modelfile**.

```bash
chmod +x start.sh
./start.sh
```

**What `start.sh` does:**
1. Installs **uv** if missing and adds it to your PATH.  
2. Creates a **Python 3.12** virtualenv via `uv venv` and installs deps from `requirements.txt`.  
3. Copies **`.env-template` → `.env`** (if `.env` doesn’t exist) so you can configure your LLM provider/model.  
4. If **Ollama** is installed and a `Modelfile` exists, runs:
   ```bash
   ollama create pii-judge -f Modelfile
   ```
   to build the local model.  
5. Prints next steps to run the backend and frontend.

> On Windows, run from **Git Bash** (or adapt the activation path shown below).

---

## 🧩 Environment (.env)

Create your environment file from the template:

```bash
cp .env-template .env
```

Open `.env` and choose **one** LLM provider:

```ini
# Choose one provider
LLM_PROVIDER=ollama            # or: openai

# If using Ollama (local)
LLM_MODEL=pii-judge            # built from Modelfile (see below)
OLLAMA_HOST=http://localhost:11434

# If using OpenAI (cloud)
OPENAI_API_KEY=                # <-- add your key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# App settings
PORT=8000
ENV=dev
```

> `start.sh` will create `.env` if missing, but **you must edit it** with your choices/keys.

---

## 🤖 Local LLM (Ollama) & `Modelfile`

Run fully local inference with **Ollama** (https://ollama.com).

1. Install Ollama.  
2. Use the provided **`Modelfile`** to bake the system rules (PII policy) into a custom model:

```bash
# From repo root
ollama create pii-judge -f Modelfile
# Optional sanity test
ollama run pii-judge
```

3. In `.env` set:
```ini
LLM_PROVIDER=ollama
LLM_MODEL=pii-judge
OLLAMA_HOST=http://localhost:11434
```

**Why this helps:** the long policy is embedded as the model’s system prompt, so requests only send the **changing input**, which is faster and cheaper.

> Example `Modelfile` (if you need a template):
```text
FROM mistral:7b-instruct
SYSTEM """
Return ONLY valid JSON with this schema:
{ "<COLUMN>": { "text": ..., "value": { "<action>": {"status":"accepted"|"rejected","value":<str|null>}, ... } }, ... }

Rules (short):
- Allowed actions: fill|mask|generalize|drop|categorize|enrich|keep
- Exactly ONE accepted action per column; others rejected
- Prefer mask/generalize for PII/IDs (PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CIN, ID_MAROC, IBAN_CODE, LOCATION, DATE_TIME)
- Never fabricate identities; non-PII fill uses mean|median|mode|approved placeholder
- Mention missingness in "text"; missingness never justifies filling PII
- If insufficient info, be conservative
- Aliases: MIBAN_CODE=IBAN_CODE
"""
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
```

---

## 🚀 Installation (manual route)

### 1) Clone

```bash
git clone https://github.com/xfightervx/presidio.git
cd presidio
```

### 2) Setup Python Environment

#### ✅ With `uv` (recommended)

```bash
# If you don’t use start.sh:
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell):
irm https://astral.sh/uv/install.ps1 | iex

uv init
echo "3.12" > .python-version
uv venv
# Linux/macOS:
source .venv/bin/activate
# Windows (Git Bash):
source .venv/Scripts/activate
uv pip install -r requirements.txt
```

If you encounter an error with `thinc`, run:

```bash
uv pip install --upgrade --force-reinstall numpy thinc spacy
```

#### ✅ With `pip` (Python 3.10–3.12)

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
source .venv/Scripts/activate
pip install -r requirements.txt
```

---

## 🔧 `start.sh` (reference)

> The repository includes a `start.sh` similar to the below. Adjust paths for your OS/shell if needed.

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1) Install uv if missing
if ! command -v uv >/dev/null 2>&1; then
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Please install uv via PowerShell:"
    echo "  irm https://astral.sh/uv/install.ps1 | iex"
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.uv/bin:$PATH"
  fi
fi

# 2) Python env + deps
echo "3.12" > .python-version
uv venv
# Try Linux/macOS first, then Windows Git Bash
(source .venv/bin/activate || source .venv/Scripts/activate)
uv pip install -r requirements.txt

# 3) .env from template
if [ ! -f .env ]; then
  cp .env-template .env
  echo "Created .env from .env-template. Please edit it to choose/configure your LLM."
fi

# 4) Build local model if Ollama & Modelfile exist
if command -v ollama >/dev/null 2>&1 && [ -f "Modelfile" ]; then
  ollama create pii-judge -f Modelfile || true
fi

echo
echo "✅ Setup complete."
echo "Next:"
echo "  1) Edit .env to set LLM_PROVIDER and model."
echo "  2) Run backend: uv run unicorn core.backend:app --port \${PORT:-8000}"
echo "  3) Run frontend: (cd gdpr-dashboard && npm install && npm run dev)"
```

---

## 🧠 Extending with Custom Entities

To add new entities to the analyzer:

1. Create a new recognizer (class or pattern) in `core/logic/`.  
2. Register it in `get_analyzer()` at the end of `core/logic.py`.

---

## 🧪 Testing

### 1) Unit Tests

Add tests under `tests/test_entities/` and use the helper `assert_recognition`.

```bash
python -m unittest discover tests/
```

### 2) Evaluation Suite

Add cases to `assets/test_dataset.json` and run:

```bash
python evaluate_recognizers.py
```

Generates precision/recall per entity.

---

## 📂 Running the CSV Masking

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

A minimal app to upload CSV files and get full recommendations.

1. Put the masking report data into `gdpr-dashboard/src/data/`  
2. Install frontend deps:
   ```bash
   npm install
   ```
3. Start dev server:
   ```bash
   npm run dev
   ```

---

## 🖥️ Backend

```bash
uv run unicorn core.backend:app --port 8000
```

> Uses `.env` to select the LLM (local Ollama or OpenAI). Ensure your `.env` is configured.

---

**ENJOY.**
