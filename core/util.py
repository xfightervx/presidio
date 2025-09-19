import math
from typing import Dict, List
import numpy as np
import pandas as pd
import json

def json_safe(x):
    if x is None:
        return None
    if isinstance(x, (str, bool, int)):
        return x
    if isinstance(x, float):
        return None if (math.isnan(x) or math.isinf(x)) else x
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(x, dict):
        return {str(k): json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [json_safe(v) for v in x]
    return str(x)

def serialize_recommendation(rec,llm_output):
    out = {}
    print(llm_output.keys())
    for key in rec.keys():
        out[key] = {}
        out[key]["manual"] = json_safe(rec[key])
        if key in llm_output.keys():
            out[key]["llm"] = json_safe(llm_output[key])
        else :
            out[key]["llm"] = "We don t have recommendation for this column"
    return out

if __name__ == "__main__":
    grouped: Dict[str, List[dict]] = {}
    df = pd.read_csv("assets/test.csv", dtype=str)
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
    try:
        with open("logs/llm_raw_response.txt", "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        raw = ""
    cleaned = raw
    if isinstance(raw, str):
        cleaned = raw.strip()
        i, j = cleaned.find("{"), cleaned.rfind("}")
        if i != -1 and j != -1:
            cleaned = cleaned[i:j+1]
    else:
        cleaned = ""
    print()
    try:
        parsed_plan = json.loads(cleaned) if cleaned else {}
        if not isinstance(parsed_plan, dict):
            parsed_plan = {}
    except Exception:
        parsed_plan = {}
    with open("logs/llm_serialized_recommendation.txt", "w", encoding="utf-8") as f:
        json.dump(serialize_recommendation(grouped, parsed_plan), f, indent=2, ensure_ascii=False)