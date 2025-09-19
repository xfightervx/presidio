"""
Recommendation generator (POC) with LLM steward review.

• Keeps all previous per-column candidate recommendations for manual review.
• Adds ONE LLM call over all columns to produce:
    1) A steward-facing summary text.
    2) A strict machine action plan in the schema:
       {
         "<COLUMN>": {
           "<action>": {"status":"accepted"|"rejected", "value":<str|null>},
           ...
         },
         ...
       }

Return payload shape:
{
  "columns": {        # <- original grouped recommendations (unchanged)
     "COL": [ {action:..., reason:..., ...}, ... ],
     ...
  },
  "llm": {
     "steward_text": str,
     "action_plan": dict
  }
}

Notes:
- Single POC-focused LLM call (no caching/security).
- Uses ask_llm(prompt) from llm_helper.py (Ollama/OpenAI decided by env).
- Input prompt enforces: missingness is informational for PII/identifiers; prefer masking; pick at most ONE accepted action per column; do not invent actions.
"""
from __future__ import annotations

import json
import pandas as pd
from typing import Dict, List, Any
import os

from .csv_pii import score_header, sample_analyze, GDPR_CATEGORIES, MIN_SCORE
from .logic import get_analyzer
from .llm_helper import ask_llm
from .util import serialize_recommendation

NA_THRESHOLD = 0.6
GENERALIZED_ENTITIES = ["DATE_TIME", "JOB_TITLE"]
_LLM_HEADER = """
SYSTEM
Return ONLY valid JSON (no Markdown fences, no text outside JSON).
Top-level keys MUST be the exact column names.
For each column, include:
- "text": 2-6 sentences for the data steward. Mention missingness if given, but for PII/identifiers missingness is informational only and does NOT justify filling.
- "value": object with ONLY the actions that were proposed for that column. For each action:
   {"status": "accepted"|"rejected", "value": <string|null>}
The output schema is:
{
  "<COLUMN>": {
    "text": {<the recommendation as a comprehensible text>},
    "value": {
        "<action>": {"status":"accepted"|"rejected", "value":<str|null>},
        ...
    }
  },
  ...
}
Rules:
- ALLOWED_ACTIONS = {fill, mask, generalize, drop, categorize, enrich, keep}
- PII/identifiers: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CIN, ID_MAROC, IBAN_CODE, LOCATION, DATE_TIME
- Prefer mask/generalize for PII/identifiers. Never suggest filling with names/emails/numbers or fabricated identities.
- Exactly ONE action per column should be "accepted"; others must be "rejected".
- "value" meaning:
   • fill → "median"|"mean"|"mode"|approved placeholder string (only for non-PII)
   • generalize → "year"|"month" etc.
   • mask/drop/categorize/enrich → usually null
- Do not invent actions that were not proposed for that column.
- If information is insufficient, be conservative and state that in "text".
- You will be provided next we a glossary of PII s and SII s be sure to include them as a reason for your decision.
{
  "VERSION": "2025-09-16",
  "DEFINITIONS": {
    "PII": "Personal data that can identify or relate to an individual but is not a GDPR Article 9 special category. Requires lawful basis, minimization, and security.",
    "SII": "Sensitive/special-category personal data (GDPR Art. 9) requiring an additional Article 9(2) condition. In Morocco (Law 09-08), 'données sensibles' typically need CNDP prior authorization."
  },
  "ALIASES": {
    "MIBAN_CODE": "IBAN_CODE"
  },
  "ENTITIES": {
    "PERSON":              {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "EMAIL_ADDRESS":       {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "PHONE_NUMBER":        {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "LOCATION":            {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "mask"},
    "POSTAL_CODE":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "generalize"},
    "DATE_TIME":           {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "generalize"},
    "DATE_OF_BIRTH":       {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "generalize"},
    "AGE":                 {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "low",    "default_action": "generalize"},
    "JOB_TITLE":           {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "mask"},
    "NATIONALITY":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "mask"},

    "CIN":                 {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "ID_MAROC":            {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "PASSPORT":            {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "DRIVER_LICENSE":      {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "INSURANCE_NUMBER":    {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "INTERNAL_ID":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "tokenize"},

    "IBAN_CODE":           {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "BANK_ACCOUNT":        {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "CREDIT_CARD":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "critical","default_action": "mask"},

    "HEALTH_DATA":         {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "MEDICAL_CONDITION":   {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "BLOOD_TYPE":          {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "GENETIC_DATA":        {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "BIOMETRIC_DATA_ID":   {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "RACIAL_ETHNIC_ORIGIN":{"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "POLITICAL_OPINION":   {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "RELIGIOUS_BELIEF":    {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "TRADE_UNION_MEMBERSHIP":{"category": "SII","gdpr": {"special_category": true}, "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "SEXUAL_ORIENTATION":  {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"}
  }
}
INPUT
"""


# ────────────────────────────────────────────────────────────────────────────
# Basic analyzers (unchanged core logic)
# ────────────────────────────────────────────────────────────────────────────

def analyze_table_na(df: pd.DataFrame) -> dict:
    """NA-based fills/drops.
    Returns {col: {action, reason, percentage, ...}}
    """
    recommendations = {}
    for column in df.columns:
        na_percentage = float(df[column].isnull().mean())
        if na_percentage == 0:
            continue
        if 0 < na_percentage < NA_THRESHOLD:
            if str(df[column].dtype) in ["float64", "int64", "Float64", "Int64"]:
                filling = {
                    "mean": float(df[column].mean()),
                    "median": float(df[column].median()),
                    "max": float(df[column].max()),
                    "min": float(df[column].min()),
                }
            else:
                try:
                    mode_val = df[column].mode(dropna=True).iloc[0]
                except Exception:
                    mode_val = None
                filling = {"mode": mode_val}
            recommendations[column] = {
                "action": "fill",
                "reason": "some values are missing",
                "percentage": na_percentage,
                "filling": filling,
            }
        else:
            recommendations[column] = {
                "action": "drop",
                "reason": "high percentage of missing values",
                "percentage": na_percentage,
            }
    return recommendations


def full_analyze(series: pd.Series, analyzer) -> dict:
    """PII scan on one column → suggest mask/generalize/keep.
    Returns a dict describing the top detected entities and suggested action.
    """
    count = 0
    entities: Dict[str, int] = {}
    for v in series:
        if pd.isna(v):
            continue
        result = analyzer.analyze(str(v), language="en")
        result = [r for r in result if r.score >= MIN_SCORE]
        if not result:
            continue
        count += 1
        for r in result:
            entities[r.entity_type] = entities.get(r.entity_type, 0) + 1

    if count == 0:
        return {
            "action": "keep",
            "reason": "no significant PII detected",
            "guessed_entity": None,
            "top_detected_entities": [],
        }

    top_entities = sorted(entities.items(), key=lambda x: x[1], reverse=True)[:3]
    top_ent = top_entities[0][0]
    return {
        "action": "mask" if top_ent not in GENERALIZED_ENTITIES else "generalize",
        "reason": "detected PII entities",
        "guessed_entity": top_ent,
        "top_detected_entities": top_entities,
        "percentage of PII": (count / max(len(series), 1)) * 100.0,
    }


def process_pii(df: pd.DataFrame) -> dict:
    """Header-aware PII classification using header scores + sample analysis.
    Returns {col: {action, reason, ...}}
    """
    recommendations: Dict[str, Any] = {}
    df = df.astype(str)
    headers = df.columns.tolist()
    rows = df.values.tolist()

    analyzer = get_analyzer()
    scores = score_header(headers, threshhold=70)
    profiled = sample_analyze(headers, rows, analyzer, scores)

    for header in headers:
        profile_info = profiled.get(header)
        if not profile_info:
            recommendations[header] = full_analyze(df[header].rename(header), analyzer)
            continue
        guessed_entity = profile_info.get("guessed_entity")
        top_entities = profile_info.get("top_detected_entities", [])
        is_confirmed = any(ent == guessed_entity and cnt > 0 for ent, cnt in top_entities)
        if is_confirmed:
            recommendations[header] = {
                "action": "mask" if guessed_entity not in GENERALIZED_ENTITIES else "generalize",
                "reason": f"confirmed PII entity: {guessed_entity}",
                "gdpr_category": GDPR_CATEGORIES.get(guessed_entity, "Uncategorized"),
                "top_entities": top_entities,
            }
        else:
            recommendations[header] = full_analyze(df[header], analyzer)
    return recommendations

# Enrichment (header clustering) — unchanged POC
with open("models/header_encoder.pkl", "rb") as f:
    sentence_model = pd.read_pickle(f)  # as given in your base code
with open("models/kmeans_headers.pkl", "rb") as f:
    kmeans_model = pd.read_pickle(f)
with open("models/pca_transform.pkl", "rb") as f:
    pca_model = pd.read_pickle(f)

ENRICHABLE_HEADERS = [2]

def enrich_headers(df: pd.DataFrame) -> dict:
    enrichable = {}
    for header in df.columns:
        embedding = sentence_model.encode([header])
        embedding = pca_model.transform(embedding)
        cluster = int(kmeans_model.predict(embedding)[0])
        if cluster in ENRICHABLE_HEADERS:
            enrichable[header] = {
                "action": "enrich",
                "reason": "header matches enrichable cluster",
                "cluster": cluster,
                "suggestions": [
                    "join external source",
                    "derive from related field",
                    "add semantic tag",
                ],
            }
        else:
            enrichable[header] = {
                "action": "keep",
                "reason": "no enrichment recommended",
                "cluster": cluster,
            }
    return enrichable

UNIQNESS_THRESHOLD = 0.05
MAX_UNIQUE_ABSOLUTE = 50

def analyze_categorization(df: pd.DataFrame) -> dict:
    recommendations = {}
    total_rows = len(df)
    for column in df.columns:
        if total_rows == 0:
            continue
        unique_count = int(df[column].nunique(dropna=True))
        uniqueness_ratio = unique_count / total_rows
        if (uniqueness_ratio <= UNIQNESS_THRESHOLD) and (unique_count <= MAX_UNIQUE_ABSOLUTE):
            top_values = {k: int(v) for k, v in df[column].value_counts().head(5).to_dict().items()}
            recommendations[column] = {
                "action": "categorize",
                "reason": f"Low uniqueness ratio ({uniqueness_ratio:.2f}) and unique count ({unique_count})",
                "uniqueness_ratio": uniqueness_ratio,
                "unique_count": unique_count,
                "example_categories": top_values,
            }
    return recommendations

# ────────────────────────────────────────────────────────────────────────────
# LLM prompt construction & parsing
# ────────────────────────────────────────────────────────────────────────────

def _summarize_extra(rec: dict) -> str:
    keys = [
        "percentage", "filling", "gdpr_category", "guessed_entity",
        "top_entities", "top_detected_entities", "cluster",
        "percentage of PII", "uniqueness_ratio", "unique_count",
    ]
    parts: List[str] = []
    for k in keys:
        if k in rec:
            v = rec[k]
            if isinstance(v, (list, dict)):
                s = str(v)[:300]
            else:
                s = str(v)
            parts.append(f"{k}={s}")
    return "; ".join(parts) if parts else "none"


_LLM_HEADER = """
SYSTEM
Return ONLY valid JSON (no Markdown fences, no text outside JSON).
Top-level keys MUST be the exact column names.
For each column, include:
- "text": 2-6 sentences for the data steward. Mention missingness if given, but for PII/identifiers missingness is informational only and does NOT justify filling.
- "value": object with ONLY the actions that were proposed for that column. For each action:
   {"status": "accepted"|"rejected", "value": <string|null>}
The output schema is:
{
  "<COLUMN>": {
    "text": {<the recommendation as a comprehensible text>},
    "value": {
        "<action>": {"status":"accepted"|"rejected", "value":<str|null>},
        ...
    }
  },
  ...
}
Rules:
- ALLOWED_ACTIONS = {fill, mask, generalize, drop, categorize, enrich, keep}
- PII/identifiers: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CIN, ID_MAROC, IBAN_CODE, LOCATION, DATE_TIME
- Prefer mask/generalize for PII/identifiers. Never suggest filling with names/emails/numbers or fabricated identities.
- Exactly ONE action per column should be "accepted"; others must be "rejected".
- "value" meaning:
   • fill → "median"|"mean"|"mode"|approved placeholder string (only for non-PII)
   • generalize → "year"|"month" etc.
   • mask/drop/categorize/enrich → usually null
- Do not invent actions that were not proposed for that column.
- If information is insufficient, be conservative and state that in "text".
- You will be provided next we a glossary of PII s and SII s be sure to include them as a reason for your decision.
{
  "VERSION": "2025-09-16",
  "DEFINITIONS": {
    "PII": "Personal data that can identify or relate to an individual but is not a GDPR Article 9 special category. Requires lawful basis, minimization, and security.",
    "SII": "Sensitive/special-category personal data (GDPR Art. 9) requiring an additional Article 9(2) condition. In Morocco (Law 09-08), 'données sensibles' typically need CNDP prior authorization."
  },
  "ALIASES": {
    "MIBAN_CODE": "IBAN_CODE"
  },
  "ENTITIES": {
    "PERSON":              {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "EMAIL_ADDRESS":       {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "PHONE_NUMBER":        {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "LOCATION":            {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "mask"},
    "POSTAL_CODE":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "generalize"},
    "DATE_TIME":           {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "generalize"},
    "DATE_OF_BIRTH":       {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "generalize"},
    "AGE":                 {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "low",    "default_action": "generalize"},
    "JOB_TITLE":           {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "mask"},
    "NATIONALITY":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "mask"},

    "CIN":                 {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "ID_MAROC":            {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "PASSPORT":            {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "DRIVER_LICENSE":      {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "INSURANCE_NUMBER":    {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "INTERNAL_ID":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "medium", "default_action": "tokenize"},

    "IBAN_CODE":           {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "BANK_ACCOUNT":        {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "high",   "default_action": "mask"},
    "CREDIT_CARD":         {"category": "PII", "gdpr": {"special_category": false}, "ma_0908": {"sensitive": false, "authorization_required": false}, "risk": "critical","default_action": "mask"},

    "HEALTH_DATA":         {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "MEDICAL_CONDITION":   {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "BLOOD_TYPE":          {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "GENETIC_DATA":        {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "BIOMETRIC_DATA_ID":   {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"},
    "RACIAL_ETHNIC_ORIGIN":{"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "POLITICAL_OPINION":   {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "RELIGIOUS_BELIEF":    {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "TRADE_UNION_MEMBERSHIP":{"category": "SII","gdpr": {"special_category": true}, "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "high",   "default_action": "mask"},
    "SEXUAL_ORIENTATION":  {"category": "SII", "gdpr": {"special_category": true},  "ma_0908": {"sensitive": true,  "authorization_required": true},  "risk": "critical","default_action": "mask"}
  }
}
INPUT
""".strip()



def recommend_actions(df: pd.DataFrame) -> dict:
    """Run analyzers → group candidates → call LLM once → return combined payload.

    Returns
    -------
    dict with keys:
      - columns: original grouped candidates for manual review
      - llm: { steward_text, action_plan }
    """
    grouped: Dict[str, List[dict]] = {}

    # Run all analyzers
    na_results = analyze_table_na(df)
    pii_results = process_pii(df)
    enrich_results = enrich_headers(df)
    categorize_results = analyze_categorization(df)
    all_results: Dict[str, List[dict]] = {}
    for results_dict in [na_results, pii_results, enrich_results, categorize_results]:
        for col, rec in results_dict.items():
            all_results.setdefault(col, []).append(rec)
    for col, recs in all_results.items():
        filtered = [r for r in recs if r.get("action") != "keep"]
        if filtered:
            grouped[col] = filtered

    prompt = _LLM_HEADER + "\n" + str(grouped)
    raw = ask_llm(prompt)
    cleaned = raw
    if isinstance(raw, str):
        cleaned = raw.strip()
        i, j = cleaned.find("{"), cleaned.rfind("}")
        if i != -1 and j != -1:
            cleaned = cleaned[i:j+1]
    else:
        cleaned = ""

    try:
        parsed_plan = json.loads(cleaned) if cleaned else {}
        if not isinstance(parsed_plan, dict):
            parsed_plan = {}
    except Exception:
        parsed_plan = {}

    try:
        with open("logs/recommendations.log", "w", encoding="utf-8", errors="replace") as f:
            f.write("=== PROMPT ===\n" + prompt + "\n\n")
            f.write("===GROUPED===\n" + str(grouped) + "\n\n")
            f.write("=== RAW ===\n" + (raw or "") + "\n\n")
    except Exception:
        pass
    return serialize_recommendation(grouped, parsed_plan)



