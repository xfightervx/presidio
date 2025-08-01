from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from .recommendation import recommend_actions
from fastapi.responses import JSONResponse
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

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"error": "Only CSV files are supported."}

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        return {"error": f"Failed to parse CSV: {str(e)}"}

    recommendations = recommend_actions(df)
    return JSONResponse(content=recommendations)
