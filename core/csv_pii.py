import pandas as pd
import json
from rapidfuzz.fuzz import token_set_ratio
from logic import get_analyzer
from collections import defaultdict
csv_file = pd.read_csv("assets/test.csv")

headers = csv_file.columns.tolist()
with open("assets/rgdp_glossary.json") as f:
    GDPR_CATEGORIES = json.load(f)

MIN_SCORE = 0.6
def score_header(headers, threshhold=70):
    with open("assets/entities_synonymes.json") as f:
        ENTITY_SYNONYMS = json.load(f)
    header_match = {}
    for header in headers:
        header_clean = header.strip().lower().replace("_", "").replace(" ", "")
        best_match = None
        best_score = 0
        for entity, synonyms in ENTITY_SYNONYMS.items():
            for syn in synonyms:
                syn_cleaned = syn.strip().lower().replace("_", "").replace(" ", "")
                score = token_set_ratio(header_clean, syn_cleaned)
                if score > best_score:
                    best_score = score
                    best_match = entity
        if best_score >= threshhold:
            header_match[header] = {"entity":best_match, "score": best_score}
        else:
            header_match[header] = {"entity": None, "score": best_score}
    return header_match


scores = score_header(headers, threshhold=70)

def adaptive_sampling(rows, threshold=0.3, min_samples=30):
    length = len(rows)
    if length < min_samples:
        return rows
    return rows[:min(int(length * threshold), min_samples)]

def sample_analyze(headers, rows, analyzer, scores):
    profiled = {}
    simple = adaptive_sampling(rows)
    for idx, header in enumerate(headers):
        if header not in scores or scores[header]["entity"] is None:
            continue
        entity = defaultdict(int)
        entity_det = []

        for row in simple:
            if idx >= len(row):
                continue
            cell = row[idx]
            if pd.isna(cell):
                continue
            results = analyzer.analyze(text=str(cell), language="en")
            filtred = [r for r in results if r.score >= MIN_SCORE]

            for r in filtred:
                entity[r.entity_type] += 1
            
            entity_det.append(
                {"Text" : cell,
                "entities" : [r.to_dict() for r in filtred]}
            )

        hits = sorted(entity.items(), key=lambda x: x[1], reverse=True)
        profiled[header] = {
            "index": idx,
            "guessed_entity": scores[header]["entity"],
            "similarity_score": scores[header]["score"],
            "top_detected_entities": hits,
            "samples": entity_det
        }
    return profiled

def full_analyze_mask(column, analyzer):
    masked = []
    for cell in column:
        if pd.isna(cell):
            masked.append(None)
            continue
        cell = str(cell)
        results = analyzer.analyze(text=str(cell), language="en")
        results = [r for r in results if r.score >= MIN_SCORE]

        selected = []
        results.sort(key=lambda x: (x.start,-x.end))
        prev = None
        for r in results:
            if not prev:
                prev = r
                continue
            if r.start < prev.end:
                prev_span = prev.end - prev.start
                r_span = r.end - r.start
                if r_span > prev_span or (r_span == prev_span and r.score > prev.score):
                    prev = r
            else:
                selected.append(prev)
                prev = r
        if prev:
            selected.append(prev)
            for r in selected:
                cat = GDPR_CATEGORIES.get(r.entity_type, "Uncategorized")
                report[column.name][cat] += 1
        masked_text = mask(cell, selected)
        masked.append(masked_text)
    return masked

report = defaultdict(lambda: defaultdict(int))
def mask(text: str, entities):
    masked = ""
    last_end = 0
    for entity in entities:
        start = entity.start if hasattr(entity, "start") else entity["start"]
        end_pos = entity.end if hasattr(entity, "end") else entity["end"]
        label = entity.entity_type if hasattr(entity, "entity_type") else entity["entity_type"]
        category = GDPR_CATEGORIES.get(label, "Uncategorized")

        masked += text[last_end:start]
        masked += f"<{category}>"
        last_end = end_pos

    masked += text[last_end:]
    return masked


def process_csv(csv_path):
    df = pd.read_csv(csv_path, dtype=str)
    headers = df.columns.tolist()
    rows = df.values.tolist()
    analyzer = get_analyzer()

    scores = score_header(headers, threshhold=70)

    profiled = sample_analyze(headers, rows, analyzer, scores)

    for header in headers:
        profile_info = profiled.get(header)
        if not profile_info:
            df[header] = full_analyze_mask(df[header].rename(header) ,analyzer)
            continue
        guessed_entity = profile_info["guessed_entity"]
        top_entities = profile_info["top_detected_entities"]
        is_confirmed = any(
            ent == guessed_entity and count > 0 for ent, count in top_entities
        )
        if is_confirmed:
            df[header] = df[header].apply(
                lambda x: f"<{guessed_entity}>" if pd.notna(x) else x
            )
        else:
            df[header] = full_analyze_mask(df[header], analyzer)

    return df,report



masked_df,masking_report = process_csv("assets/test.csv")
masked_df.to_csv("assets/masked_test.csv", index=False)
with open("assets/masking_report.json", "w") as f:
    json.dump(masking_report, f, indent=2)