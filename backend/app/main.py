from typing import Union

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(__file__))  # Ensure import from app directory
from psm import run_psm
import json

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/api/psm")
async def psm_api(
    experiment: UploadFile = File(...),
    control: UploadFile = File(...),
    columns: str | None = Form(None),
):
    exp_df = pd.read_csv(experiment.file)
    ctrl_df = pd.read_csv(control.file)
    if list(exp_df.columns) != list(ctrl_df.columns):
        raise HTTPException(status_code=400, detail="两个文件的表头不一致")
    selected_cols = None
    if columns:
        try:
            selected_cols = json.loads(columns)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="列信息解析失败")
    try:
        matched = run_psm(exp_df, ctrl_df, selected_cols)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")
    # 只返回前100行，防止数据过大
    return {
        "columns": list(matched.columns),
        "data": matched.head(100).to_dict(orient="records")
    }

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
