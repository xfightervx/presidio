import math
import numpy as np
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
    for key in rec:
        out[key] = {}
        out[key]["manual"] = json_safe(rec[key])
        if key in llm_output:
            out[key]["llm"] = json_safe(llm_output[key])
        else :
            out[key]["llm"] = "We don t have recommendation for this column"
    return out

if __name__ == "__main__":
    with open('logs/recommendations.json', 'r') as f:
        recommendations = json.load(f)
    with open('assets/json_serialization_test.json', 'r') as f:
        llm_output = json.load(f)
    with open('logs/json_serialization_test_output.json', 'w') as f:
        json.dump(serialize_recommendation(recommendations,llm_output), f, indent=2)