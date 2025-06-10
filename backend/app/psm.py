import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from typing import List, Optional

def run_psm(
    exp_df: pd.DataFrame,
    ctrl_df: pd.DataFrame,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """根据给定列执行倾向性得分匹配并返回匹配后的对照组数据"""

    # 检查表头一致
    if list(exp_df.columns) != list(ctrl_df.columns):
        raise ValueError("实验组和对照组的表头不一致")

    # 处理选择的列
    if columns is not None:
        for col in columns:
            if col not in exp_df.columns:
                raise ValueError(f"选择的列不存在: {col}")
    else:
        columns = list(exp_df.columns)

    # 模型数据仅保留选择的列
    exp_model = exp_df[columns].copy()
    ctrl_model = ctrl_df[columns].copy()
    exp_model["treatment"] = 1
    ctrl_model["treatment"] = 0
    data = pd.concat([exp_model, ctrl_model], ignore_index=True)

    # 估计倾向性得分
    X = data[columns]
    T = data["treatment"]
    model = LogisticRegression(max_iter=1000)
    model.fit(X, T)
    data["propensity_score"] = model.predict_proba(X)[:, 1]

    # 最近邻匹配
    exp_scores = data[data["treatment"] == 1]["propensity_score"].values.reshape(
        -1, 1
    )
    ctrl_scores = data[data["treatment"] == 0]["propensity_score"].values.reshape(
        -1, 1
    )
    nn = NearestNeighbors(n_neighbors=1, algorithm="auto").fit(ctrl_scores)
    _, indices = nn.kneighbors(exp_scores)
    matched_ctrl_indices = (
        data[data["treatment"] == 0].iloc[indices.flatten()].index
    )

    # 返回原始对照组中与实验组匹配的行
    matched_ctrl = ctrl_df.loc[matched_ctrl_indices]
    return matched_ctrl.reset_index(drop=True)
