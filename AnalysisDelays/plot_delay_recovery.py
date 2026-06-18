#!/usr/bin/env python3
"""
晚点恢复能力可视化脚本
=======================
绘制各事件列车在各车站的晚点时间柱状图，用于展示晚点恢复能力。

输入:
    - plan_path: 计划时刻表 Excel 文件路径
    - reschedule_path: 实际/扰动后时刻表 Excel 文件路径
    - event_csv_path: 主要扰动事件 CSV 文件路径（只展示这些列车）

输出:
    - 柱状图，横轴为车站名称，纵轴为晚点时间（秒），不同事件/列车用不同颜色分组

适用场景:
    修改顶部的路径配置即可复用于不同的 S1_t1, S1_t2, ... 等场景目录。
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

# 配置区域已移动到 testconfig.py 模块
from testconfig import PLAN_PATH, RESCHEDULE_PATH, EVENT_CSV_PATH, OUTPUT_DIR

# 全局绘图设置 —— 中文字体
matplotlib.rcParams["axes.unicode_minus"] = False
_CJK_FONT_CANDIDATES = [
    "AR PL UKai CN",           # AR PL UKai 楷体（含 ASCII + CJK）
    "AR PL UMing CN",          # AR PL UMing 明体（含 ASCII + CJK）
    "Noto Sans CJK JP",        # Noto Sans CJK（含 ASCII + 简体字）
    "WenQuanYi Micro Hei",     # 文泉驿微米黑
    "Noto Sans CJK SC",        # Noto Sans CJK 简体
]

_loaded_font = None
for _font in _CJK_FONT_CANDIDATES:
    try:
        matplotlib.font_manager.findfont(_font, fallback_to_default=False)
        matplotlib.rcParams["font.sans-serif"] = [_font] + matplotlib.rcParams.get("font.sans-serif", [])
        matplotlib.rcParams["font.family"] = "sans-serif"
        _loaded_font = _font
        break
    except Exception:
        continue

if _loaded_font is None:
    print("警告: 未找到中文字体，图表中文可能显示为方块")
else:
    print(f"使用字体: {_loaded_font}")


def load_timetable(path: str) -> pd.DataFrame:
    """读取时刻表 Excel 文件。

    Parameters
    ----------
    path : str
        Excel 文件路径

    Returns
    -------
    pd.DataFrame
        包含 NODE_ID, NODE_CODE, NODE_NAME 及各列车时间列的数据框
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"时刻表文件不存在: {path}")
    return pd.read_excel(path)


def load_event_trains(csv_path: str) -> pd.DataFrame:
    """读取主要扰动事件 CSV 文件。

    Parameters
    ----------
    csv_path : str
        CSV 文件路径

    Returns
    -------
    pd.DataFrame
        包含 事件编码, 车次号, 时间类型 等列的数据框
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"事件文件不存在: {csv_path}")
    return pd.read_csv(csv_path)


def extract_train_column_names(events_df: pd.DataFrame) -> list[str]:
    """从事件表中提取需要展示的列车列名。

    列名格式为 ``{车次号}_{时间类型}``，例如 ``G117_A``。

    Parameters
    ----------
    events_df : pd.DataFrame
        事件数据框，必须包含 ``车次号`` 和 ``时间类型（a到/d发）`` 列

    Returns
    -------
    list[str]
        时刻表中对应的列名列表
    """
    columns = []
    for _, row in events_df.iterrows():
        train = row["车次号"]
        time_type = row["时间类型（a到/d发）"].strip().upper()
        col_name = f"{train}_{time_type}"
        columns.append(col_name)
    return columns


def compute_delay_matrix(
    plan_df: pd.DataFrame,
    reschedule_df: pd.DataFrame,
    train_columns: list[str],
    events_df: pd.DataFrame,
) -> pd.DataFrame:
    """计算各事件列车在各车站的晚点时间矩阵。

    Parameters
    ----------
    plan_df : pd.DataFrame
        计划时刻表
    reschedule_df : pd.DataFrame
        实际时刻表
    train_columns : list[str]
        需要计算的列车列名列表
    events_df : pd.DataFrame
        事件数据框，用于生成标签

    Returns
    -------
    pd.DataFrame
        行为车站名，列为事件标签，值为晚点时间（秒）
    """
    stations = reschedule_df["NODE_NAME"].tolist()
    delay_matrix = pd.DataFrame(index=stations)

    for idx, col in enumerate(train_columns):
        if col not in plan_df.columns:
            raise KeyError(f"计划表中缺少列: {col}")
        if col not in reschedule_df.columns:
            raise KeyError(f"实际表中缺少列: {col}")

        plan_times = plan_df[col]
        reschedule_times = reschedule_df[col]
        delay_seconds = (reschedule_times - plan_times).dt.total_seconds()

        event_row = events_df.iloc[idx]
        time_type = event_row["时间类型（a到/d发）"].strip().upper()
        label = (
            f"#{int(event_row['事件编码'])} "
            f"{event_row['车次号']}"
            f"({'到' if time_type == 'A' else '发'})"
        )

        delay_matrix[label] = delay_seconds.values

    return delay_matrix


# TODO：改名 plotStaionDelays_for_PrimaryDelayTrains()
# 新建一个 plotStationdelays_AllTrains()，用于绘制所有列车的晚点恢复能力图
def plot_delay_recovery(
    delay_matrix: pd.DataFrame,
    events_df: pd.DataFrame,
    output_path: str,
    title: str = "晚点恢复能力分析",
    figsize: tuple = (22, 10),
) -> None:
    """绘制晚点恢复能力柱状图。

    横轴为车站（按线路顺序排列），纵轴为晚点时间（秒）。
    每个事件列车用一组柱表示，扰动起始站用红色星号标注。

    Parameters
    ----------
    delay_matrix : pd.DataFrame
        由 ``compute_delay_matrix`` 产生的晚点矩阵
    events_df : pd.DataFrame
        事件数据框，需含 ``扰动车站索引`` 列（0-based 行号）
    output_path : str
        图片输出路径
    title : str
        图表标题
    figsize : tuple
        图片尺寸 (width, height)
    """
    stations = delay_matrix.index.tolist()
    event_labels = delay_matrix.columns.tolist()
    n_stations = len(stations)
    n_events = len(event_labels)

    # 颜色映射
    cmap = plt.get_cmap("tab10", n_events)
    colors = [cmap(i) for i in range(n_events)]

    # 柱状图布局参数
    #   group_width: 每组柱子的总跨度，必须 < 1.0 否则相邻车站柱子重叠
    #   bar_width:   单根柱子宽度（在 group_width 内均分）
    group_width = 0.92
    bar_width = group_width / n_events
    x_positions = np.arange(n_stations)

    fig, ax = plt.subplots(figsize=figsize)

    for i, label in enumerate(event_labels):
        delays = delay_matrix[label].values  # seconds
        offset = (i - (n_events - 1) / 2) * bar_width
        bars = ax.bar(
            x_positions + offset,
            delays,
            width=bar_width * 0.95,  # 柱间留微小缝隙
            color=colors[i],
            label=label,
            edgecolor="white",
            linewidth=0.5,
        )

        # 在延迟 ≥ 60 秒的柱上标注分钟数
        for bar, secs in zip(bars, delays):
            if not np.isnan(secs) and abs(secs) >= 60:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + max(delay_matrix.max().max() * 0.02, 10),
                    f"{secs / 60:.0f}min",
                    ha="center",
                    va="bottom",
                    fontsize=19,
                    rotation=90,
                )

        # 标注扰动起始车站（红色星号 + 事件编号）
        # 扰动车站索引 = 时刻表中的 0-based 行号
        event_row = events_df.iloc[i]
        event_code = int(event_row["事件编码"])
        disturb_row_idx = int(event_row["扰动车站索引"])
        if 0 <= disturb_row_idx < n_stations:
            dx = x_positions[disturb_row_idx] + offset
            dy = delays[disturb_row_idx]
            if not np.isnan(dy):
                ax.scatter(
                    dx, dy,
                    marker="*", s=150, color="red", zorder=10,
                    edgecolors="darkred", linewidths=0.8,
                )
                ax.annotate(
                    f"事件{event_code}",
                    xy=(dx, dy),
                    xytext=(10, 10),
                    textcoords="offset points",
                    fontsize=19,
                    color="red",
                    fontweight="bold",
                    va="bottom",
                    ha="left",
                )

    ax.set_xlabel("车站", fontsize=14)
    ax.set_ylabel("晚点时间（秒）", fontsize=14)
    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(stations, rotation=45, ha="right", fontsize=11)
    ax.axhline(y=0, color="black", linewidth=0.8)
    ax.legend(loc="upper right", fontsize=10, ncol=1)
    ax.grid(axis="y", alpha=0.3)
    ax.set_xlim(-0.5, n_stations - 0.5)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"图表已保存至: {output_path}")


def print_delay_summary(delay_matrix: pd.DataFrame) -> None:
    """打印晚点数据的摘要统计。"""
    print("\n========== 晚点统计摘要 ==========")
    for label in delay_matrix.columns:
        delays = delay_matrix[label]
        valid = delays.dropna()
        if len(valid) == 0:
            print(f"{label}: 无有效数据")
            continue
        print(f"{label}:")
        print(f"  最大晚点: {valid.max():.0f} 秒 ({valid.max()/60:.1f} 分钟)")
        print(f"  最终晚点: {valid.iloc[-1]:.0f} 秒 ({valid.iloc[-1]/60:.1f} 分钟)")
        if pd.notna(valid.max()) and valid.max() > 0:
            recovery = (valid.max() - valid.iloc[-1]) / valid.max() * 100
            print(f"  恢复比例: {recovery:.1f}%")
    print("==================================\n")


def main():
    """主流程：读取数据 → 计算晚点 → 绘制图表。"""
    print("=" * 60)
    print("  晚点恢复能力分析")
    print("=" * 60)

    # 1. 加载数据
    print(f"\n[1/4] 加载计划时刻表: {PLAN_PATH}")
    plan_df = load_timetable(PLAN_PATH)

    print(f"[2/4] 加载实际时刻表: {RESCHEDULE_PATH}")
    reschedule_df = load_timetable(RESCHEDULE_PATH)

    print(f"[3/4] 加载事件列表: {EVENT_CSV_PATH}")
    events_df = load_event_trains(EVENT_CSV_PATH)
    print(f"  共 {len(events_df)} 个主要扰动事件:")
    for _, row in events_df.iterrows():
        print(
            f"    #{int(row['事件编码'])} {row['车次号']} "
            f"{'到' if row['时间类型（a到/d发）'].strip().upper() == 'A' else '发'} "
            f"(初始晚点 {row['晚点（秒）']}s)"
        )

    # 2. 解析要展示的列车-时间列
    train_columns = extract_train_column_names(events_df)
    print(f"  对应时刻表列: {train_columns}")

    # 3. 计算晚点矩阵
    print(f"\n[4/4] 计算晚点矩阵并绘图...")
    delay_matrix = compute_delay_matrix(
        plan_df, reschedule_df, train_columns, events_df
    )

    # 4. 打印摘要
    print_delay_summary(delay_matrix)

    # 5. 绘图
    output_path = os.path.join(OUTPUT_DIR, "delay_recovery.png")
    plot_delay_recovery(
        delay_matrix,
        events_df,
        output_path,
        title="晚点恢复能力 — S1_t1 场景",
    )

    # 同时保存 CSV
    csv_output = os.path.join(OUTPUT_DIR, "delay_matrix.csv")
    delay_matrix.to_csv(csv_output, encoding="utf-8-sig")
    print(f"晚点矩阵已保存至: {csv_output}")

    print("\n完成！")


if __name__ == "__main__":
    main()
