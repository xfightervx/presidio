from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from .recommendation import recommend_actions
from fastapi.responses import JSONResponse, StreamingResponse
import numpy as np
import json
from core.data_steward import apply_recommendations
from core.data_quality import quality

"""
this is a simple FastAPI application that allows users to upload a CSV file
and receive recommendations based on the data in the file.
i opted not to go for a more complex setup since the calls to the recommendation engine
are expected to be lightweight and the data processing is straightforward.
"""
app = FastAPI(title="Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def flatten_recommendations(column_actions: dict) -> list:
    """
    this function flattens the recommendations (it was introduced later into the devoloppement for compatibility reasons)
    Parameters:
      - column_actions: A dictionary where keys are column names and values are lists of action dictionaries.

    Returns:
      - A flattened list of action dictionaries with the corresponding column name added.
    """
    all_recommendations = []
    for col, actions in column_actions.items():
        for act in actions:
            act["column"] = col
            # Convert np.float64 to native float
            for k, v in act.items():
                if isinstance(v, (np.float32, np.float64)):
                    act[k] = float(v)
            all_recommendations.append(act)
    return all_recommendations

@app.post("/recommend")
async def recommend(file: UploadFile = File(...)):
    """
    Endpoint to receive a CSV file and return recommendations.
    """
    try:
        df = pd.read_csv(file.file)
        recommendations = recommend_actions(df)
        flatted = flatten_recommendations(recommendations)
        with open("logs/recommendations.json", "w") as f:
            json.dump(flatted, f, indent=2)
        return JSONResponse(content=flatted)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/feedback")
async def post_feedback(request: Request):
    """
    Accepts multipart/form-data with:
      - file: CSV UploadFile
      - feedback: JSON string

    Returns a downloadable CSV with applied changes.
    """
    try:
        form = await request.form()
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid form: {e}"})

    uploaded = form.get("file", None)
    feedback_str = form.get("feedback", None)

    if uploaded is None:
        return JSONResponse(status_code=422, content={"error": "Missing 'file' field."})
    if feedback_str is None:
        return JSONResponse(status_code=422, content={"error": "Missing 'feedback' field."})

    try:
        df = pd.read_csv(uploaded.file, dtype=str)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Could not read CSV: {e}"})

    try:
        feedback = json.loads(feedback_str)
        with open("logs/feedback.json", "w") as f:
            json.dump(feedback, f, indent=2)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid JSON in 'feedback': {e}"})

    try:
        new_df = apply_recommendations(df, feedback, jobs_csv_path="assets/generelized_jobs.csv")
    except FileNotFoundError as e:
        return JSONResponse(status_code=500, content={"error": f"Missing resource: {e}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Apply failed: {e}"})

    buf = io.StringIO()
    new_df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="stewarded_result.csv"'},
    )

@app.post("/quality")
async def get_quality_indicators(file: UploadFile = File(...)):
    """Receive CSV file and return comprehensive data quality indicators"""
    try:
        # Ensure it's a CSV
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are supported.")

        # Read the file content
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
        
        # Read file into pandas DataFrame
        df = pd.read_csv(io.BytesIO(raw))

        # Compute comprehensive quality indicators using our enhanced function
        indicators = quality(df)

        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj

        # Clean the indicators for JSON response
        clean_indicators = convert_numpy_types(indicators)

        return {"indicators": clean_indicators}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")