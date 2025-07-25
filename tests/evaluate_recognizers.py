import json
from core import get_analyzer

def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def iob_match(preds, gts, entity_label, text):
    tp = fp = fn = 0
    matched = []

    filtered_preds = [
        pred for pred in preds if pred.entity_type == entity_label and pred.score >= 0.5
    ]

    for pred in filtered_preds:
        match_found = False
        for gt in gts:
            if gt["entity_type"] != entity_label:
                continue
            if pred.start == gt["start"] and pred.end == gt["end"]:
                match_found = True
                matched.append((gt["start"], gt["end"]))
                break
        if match_found:
            tp += 1
        else:
            fp += 1
            print(f"[FP] {entity_label} → \"{text[pred.start:pred.end]}\" at [{pred.start}:{pred.end}] score={pred.score:.2f}")

    for gt in gts:
        if gt["entity_type"] != entity_label:
            continue
        if (gt["start"], gt["end"]) not in matched:
            fn += 1
            print(f"[FN] {entity_label} → MISSING \"{text[gt['start']:gt['end']]}\" at [{gt['start']}:{gt['end']}]")

    return tp, fp, fn

def evaluate(dataset, analyzer, entity_label):
    total_tp = total_fp = total_fn = 0

    for example in dataset:
        text = example["text"]
        ground_truths = example["entities"]
        predictions = analyzer.analyze(text=text, language="en")

        tp, fp, fn = iob_match(predictions, ground_truths, entity_label, text)
        total_tp += tp
        total_fp += fp
        total_fn += fn

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "Entity": entity_label,
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1-score": round(f1, 4),
        "TP": total_tp,
        "FP": total_fp,
        "FN": total_fn,
    }, total_tp, total_fp, total_fn


if __name__ == "__main__":
    dataset = load_dataset("tests/test_dataset.json")
    analyzer = get_analyzer()

    entities_to_evaluate = {
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "CREDIT_CARD",
        "GENDER_DECLARED",
        "IMPLIED_GENDER",
        "MEDICAL_CONDITION",
        "BLOOD_TYPE",
        "MIBAN_CODE",
        "JOB_TITLE",
        "INSURANCE_NUMBER",
        "DRIVER_LICENSE",
        "INCOME_AMOUNT",
        "PASSPORT",
        "POSTAL_CODE",
        "INTERNAL_ID",
    }

    total_tp = total_fp = total_fn = 0

    print("\n=== Evaluation Results ===\n")
    for entity in entities_to_evaluate:
        print(f"\n--- Evaluating: {entity} ---")
        metrics, tp, fp, fn = evaluate(dataset, analyzer, entity)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        print(json.dumps(metrics, indent=2))

    # Aggregate score
    agg_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    agg_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    agg_f1 = (
        2 * agg_precision * agg_recall / (agg_precision + agg_recall)
        if (agg_precision + agg_recall) > 0
        else 0.0
    )

    print("\n=== Overall Analyzer Score ===\n")
    print(json.dumps({
        "Precision": round(agg_precision, 4),
        "Recall": round(agg_recall, 4),
        "F1-score": round(agg_f1, 4),
        "TP": total_tp,
        "FP": total_fp,
        "FN": total_fn,
    }, indent=2))
