import re
import math
import json
import pandas as pd
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime

from .logic import get_analyzer
from .csv_pii import full_analyze_mask  # uses analyzer to mask per-cell


def to_number_if_possible(x: str):
    """
    try to convert a string to a number if possible
    """
    try:
        if isinstance(x, (int, float)) and not math.isnan(x):
            return x
        if isinstance(x, str):
            v = float(x) if "." in x else int(x)
            return v
    except Exception:
        pass
    return x


def load_jobs_map(csv_path: str) -> Dict[str, str]:
    """
    Load 'assets/generelized_jobs.csv' with columns: Job Title,Category
    Build a case-insensitive dict: normalized_title -> category
    """
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    mapping = {}
    for _, row in df.iterrows():
        title = row.get("Job Title", "").strip().lower()
        cat = row.get("Category", "").strip()
        if title:
            mapping[title] = cat
    return mapping


def generalize_job_from_map(title: str, jobs_map: Dict[str, str], default="other"):
    """
    Generalize job title using the jobs mapping.
    The mapping was generated so it might contain errors
    """
    if title is None or (isinstance(title, float) and math.isnan(title)):
        return title
    t = str(title).strip().lower()
    return jobs_map.get(t, default)


# Regex only used as fallback if parsing fails
_DATE_RE = re.compile(
    r"""^\s*(
        (?:\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?)   # YYYY-MM or YYYY-MM-DD or with /
        |(?:\d{1,2}[-/]\d{1,2}[-/]\d{4})       # DD-MM-YYYY or DD/MM/YYYY
        |(?:\d{4})                             # just YYYY
    )\s*$""",
    re.VERBOSE,
)

# Common date formats we want to support
_DATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d",
    "%d-%m-%Y", "%d/%m/%Y",
    "%Y-%m", "%Y/%m",
    "%Y"
]

def generalize_date_to_decade(val: str):
    """
    Convert date to decade string:
    '1983-11-12' -> '1980s'
    '2003'       -> '2000s'
    '2025/04/04' -> '2020s'
    If parsing fails, return original.
    """
    if val is None:
        return val
    s = str(val).strip()
    # Try known formats
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            decade = (dt.year // 10) * 10
            return f"{decade}s"
        except ValueError:
            continue
    # Fallback: regex + first 4 digits
    m = _DATE_RE.match(s)
    if m:
        digits = re.findall(r"\d{4}", s)
        if digits:
            year = int(digits[0])
            decade = (year // 10) * 10
            return f"{decade}s"
    return val


def apply_recommendations(
    df: pd.DataFrame,
    feedback: Dict[str, Dict[str, Dict[str, Any]]],
    jobs_csv_path: str = "assets/generelized_jobs.csv",
) -> pd.DataFrame:
    """
    Apply steward feedback to a *copy* of df.
    """
    out = df.copy(deep=True)

    analyzer = get_analyzer()
    jobs_map = load_jobs_map(jobs_csv_path)

    # --- Drops ---
    cols_to_drop = []
    for col, actions in (feedback or {}).items():
        act = actions.get("drop")
        if act and act.get("status") == "accepted" and col in out.columns:
            cols_to_drop.append(col)
    if cols_to_drop:
        out = out.drop(columns=[c for c in cols_to_drop if c in out.columns])

    # --- Other actions ---
    for col, actions in (feedback or {}).items():
        if col not in out.columns:
            continue

        # Fill
        fill_cfg = actions.get("fill")
        if fill_cfg and fill_cfg.get("status") == "accepted":
            choice = fill_cfg.get("value")
            series = out[col]
            try_num = pd.to_numeric(series, errors="coerce")
            numeric_ratio = try_num.notna().mean()

            if choice in {"mean", "median", "max", "min"} and numeric_ratio > 0.5:
                if choice == "mean":
                    fill_val = try_num.mean()
                elif choice == "median":
                    fill_val = try_num.median()
                elif choice == "max":
                    fill_val = try_num.max()
                else:
                    fill_val = try_num.min()
                out[col] = series.fillna(fill_val)
            elif choice == "mode":
                mode_vals = series.mode(dropna=True)
                fill_val = mode_vals.iloc[0] if not mode_vals.empty else ""
                out[col] = series.fillna(fill_val)
            else:
                custom_val = to_number_if_possible(choice)
                out[col] = series.fillna(custom_val)

        # Mask
        mask_cfg = actions.get("mask")
        if mask_cfg and mask_cfg.get("status") == "accepted":
            if analyzer is None:
                analyzer = get_analyzer()
            out[col] = pd.Series(full_analyze_mask(out[col], analyzer), index=out.index)

        # Generalize
        gen_cfg = actions.get("generalize")
        if gen_cfg and gen_cfg.get("status") == "accepted":
            sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else ""
            gen_type = "date" if _DATE_RE.match(sample_val) else "job"
            if gen_type == "job":
                out[col] = out[col].apply(lambda v: generalize_job_from_map(v, jobs_map))
            elif gen_type == "date":
                out[col] = out[col].apply(generalize_date_to_decade)
            else:
                s = out[col].astype(str)
                date_like = s.str.match(_DATE_RE).mean()
                if date_like >= 0.5:
                    out[col] = out[col].apply(generalize_date_to_decade)
                else:
                    out[col] = out[col].apply(lambda v: generalize_job_from_map(v, jobs_map))

        # Categorize
        cat_cfg = actions.get("categorize")
        if cat_cfg and cat_cfg.get("status") == "accepted":
            out[col] = out[col].astype("category")

    return out
