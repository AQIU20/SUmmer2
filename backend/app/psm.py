import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from typing import Tuple

def run_psm(exp_df: pd.DataFrame, ctrl_df: pd.DataFrame) -> pd.DataFrame:
    """
    exp_df: 实验组DataFrame
    ctrl_df: 对照组DataFrame
    返回：与实验组匹配的对照组DataFrame（与实验组行数相同，列相同）
    """
    # 检查表头
    if list(exp_df.columns) != list(ctrl_df.columns):
        raise ValueError("实验组和对照组的表头不一致")
    # 合并数据，添加treatment列
    exp = exp_df.copy()
    ctrl = ctrl_df.copy()
    exp['treatment'] = 1
    ctrl['treatment'] = 0
    data = pd.concat([exp, ctrl], ignore_index=True)
    # 特征列（全部去除treatment）
    features = [col for col in data.columns if col != 'treatment']
    X = data[features]
    T = data['treatment']
    # 1. 估计倾向性得分
    model = LogisticRegression(max_iter=1000)
    model.fit(X, T)
    propensity_scores = model.predict_proba(X)[:, 1]
    data['propensity_score'] = propensity_scores
    # 2. 最近邻匹配
    exp_scores = data[data['treatment'] == 1]['propensity_score'].values.reshape(-1, 1)
    ctrl_scores = data[data['treatment'] == 0]['propensity_score'].values.reshape(-1, 1)
    nn = NearestNeighbors(n_neighbors=1, algorithm='auto').fit(ctrl_scores)
    distances, indices = nn.kneighbors(exp_scores)
    matched_ctrl_indices = data[data['treatment'] == 0].iloc[indices.flatten()].index
    matched_ctrl = ctrl.loc[matched_ctrl_indices]
    # 返回匹配后的对照组
    return matched_ctrl.reset_index(drop=True) 