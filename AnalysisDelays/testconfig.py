"""场景测试配置模块。

将调度场景Sx测试案例tx的工作路径, 时刻表文件，日志文件等的路径与输出目录等配置集中管理，方便快速切换不同测试场景。
"""

import os

PROJECT_ROOT = os.path.expanduser(
    "/home/dell/Release_development/jh/")

SCENARIO_FOLDER = "jh_s1"
TEST_FOLDER = "S1_t1"
FILE_TT0 = "jh_s1/data/plan_TT0 .xlsx"
FILE_TTRescheduled = "jh_s1/data/S1_t1/reschedule_TT0.xlsx"
FILE_EVENT = "jh_s1/data/S1_t1/S1_test.csv"

# "/home/dell/Release_development/jh/"
PLAN_PATH = os.path.expanduser(
     PROJECT_ROOT, FILE_TT0
)

RESCHEDULE_PATH = os.path.expanduser(
    PROJECT_ROOT, FILE_TTRescheduled
)

# "/home/dell/Release_development/jh/jh_s1/data/S1_t1/S1_test.csv"
EVENT_CSV_PATH = os.path.expanduser(
   PROJECT_ROOT, FILE_EVENT)

OUTPUT_DIR = os.path.expanduser(
    PROJECT_ROOT, "jh_s1/output/S1_t1"
)
