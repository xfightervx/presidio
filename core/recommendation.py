"""
the recommendation model is thought off as follwing:
    it has to do basic stuff like replacing na values with either statistical values or a filler 
    it has to give one or more of the following action recommendations:
        mask : if it is considered as a High sensitivity PII
        generize : when having dates or ages the user should be able to generize it like from 2003-11-29 -> 2003 or 2000s
        enrich : (i m still thinking of the detailes) it should be able to ditect headers and try to map them to other infos to add to the table
        drop : give the drop column option once the column have high percentage of na values
        categorize : it the uniqueness count is low enough it should be able to categorize the column
        keep : if none of the above is applicable, it should be able to keep the column as is
"""

import pandas as pd
from .csv_pii import full_analyze_mask,score_header, sample_analyze,GDPR_CATEGORIES,MIN_SCORE
from .logic import get_analyzer
NA_THRESHOLD = 0.6


def analyze_table_na(df: pd.DataFrame) -> dict:
    """
    this function analyzes the DataFrame for missing values and returns the recommnendations for each column
    Parameters:
    df (pd.DataFrame): The DataFrame to analyze for missing values.

    Returns:
    dict: A dictionary containing recommendations for each column based on the percentage of missing values.
    1. If the percentage of missing values is below the threshold, it suggests filling the missing values with statistical measures (mean, median, mode).
    2. If the percentage of missing values is above the threshold, it suggests dropping the column.
    """
    recommendations = {}
    for column in df.columns:
        na_percentage = df[column].isnull().mean()
        if na_percentage == 0:
            continue
        if 0 < na_percentage < NA_THRESHOLD:
            if df[column].dtype in ['float64', 'int64']:
                filling = {"mean": df[column].mean(), "median": df[column].median(), "max": df[column].max(), "min": df[column].min()}
            else:
                filling = {"mode": df[column].mode()[0]}
            recommendations[column] = {
                "action": "fill",
                "reason": "some values are missing",
                "percentage": na_percentage,
                "filling": filling
            }
        else:
            recommendations[column] = {
                "action": "drop",
                "reason": "high percentage of missing values",
                "percentage": na_percentage
            }
    return recommendations


#this next function is equivalent to process csv in csv_pii.py but with dataframe as input
def process_pii(df: pd.DataFrame):
    """
    this function processes the DataFrame for PII detection and returns a dictionary with recommnendations on how to handle each column.
    Parameters:
    df (pd.DataFrame): The DataFrame to process for PII detection.
    Returns:
    dict: A dictionary containing recommendations for each column based on PII detection.
    """
    recommendations = {}
    df = df.astype(str)  # Ensure all data is treated as strings for PII detection
    headers = df.columns.tolist()
    rows = df.values.tolist()
    analyzer = get_analyzer()
    scores = score_header(headers, threshhold=70)
    profiled = sample_analyze(headers, rows, analyzer, scores)

    for header in headers:
        profile_info = profiled.get(header)
        if not profile_info:
            recommendations[header]= full_analyze(df[header].rename(header), analyzer)
            continue
        guessed_entity = profile_info["guessed_entity"]
        top_entities = profile_info["top_detected_entities"]
        is_confirmed = any(
            ent == guessed_entity and count > 0 for ent, count in top_entities
        )
        if is_confirmed:
            recommendations[header] = {
                "action": "mask",
                "reason": f"confirmed PII entity: {guessed_entity}",
                "gdpr_category": GDPR_CATEGORIES.get(guessed_entity, "Uncategorized"),
                "top_entities": top_entities
            }
        else:
            recommendations[header] = full_analyze(df[header], analyzer)

    return recommendations

#this function is equivalent to full_analyze_mask in csv_pii.py without masking and returns a Dictionary instead of masked
def full_analyze(df: pd.Series, analyzer):
    """
    this function analyzes the DataFrame column for PII detection and returns a dictionary with recommendations on how to handle the column.
    Parameters:
    df (pd.Series): The DataFrame column to analyze for PII detection.
    analyzer: The analyzer object used for PII detection.
    Returns:
    dict: A dictionary containing recommendations for the column based on PII detection.
    """
    count = 0
    entities = {}
    for row in df:
        if pd.isna(row):
            continue
        result = analyzer.analyze(row)
        result = [r for r in result if r.score >= MIN_SCORE]
        if len(result) == 0:
            continue 
        else :
            count += 1
            for r in result:
                if r.entity_type not in entities:
                    entities[r.entity_type] = 0
                entities[r.entity_type] += 1
    if count == 0:
        return {
            "action": "keep",
            "reason": "no significant PII detected",
            "guessed_entity": None,
            "top_detected_entities": []
        }
    top_entities = sorted(entities.items(), key=lambda x: x[1], reverse=True)[:3]
    return {
        "action": "mask",
        "reason": "detected PII entities",
        "guessed_entity": top_entities[0][0],
        "top_detected_entities": top_entities,
        "percentage of PII": count / len(df) * 100
    }
    

# the next step is enrichement and for that we will use k means to cluster headers to find similar ones
