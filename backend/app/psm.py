import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from typing import List, Optional


def run_psm(
    exp_df: pd.DataFrame,
    ctrl_df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    n_results: Optional[int] = None,
) -> pd.DataFrame:
    """根据给定列执行倾向性得分匹配并返回按距离排序后的对照组数据

    Parameters
    ----------
    exp_df : DataFrame
        实验组数据
    ctrl_df : DataFrame
        对照组数据
    columns : List[str] | None
        用于匹配的列，None 表示使用全部列
    n_results : int | None
        返回距离最近的前 n_results 个结果，None 表示返回全部匹配结果
    """

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
    distances, indices = nn.kneighbors(exp_scores)
    # 根据匹配结果在原始对照组中取出对应行
    matched_ctrl = ctrl_df.iloc[indices.flatten()].copy()
    matched_ctrl["match_distance"] = distances.flatten()

    # 按距离从小到大排序并限制返回数量
    matched_ctrl = matched_ctrl.sort_values("match_distance")
    if n_results is not None:
        matched_ctrl = matched_ctrl.head(int(n_results))
    return matched_ctrl.drop(columns="match_distance").reset_index(drop=True)
