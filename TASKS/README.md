# Course AI Helper - Agent Team 任务中心

## 📋 当前状态

**阶段**: 项目熟悉阶段

**协调方式**: 由 main Agent（公司小龙虾）统一协调

## 🎯 任务列表

| 任务 ID | Agent | 任务 | 状态 | 输出文件 |
|--------|-------|------|------|----------|
| 00 | architect | 系统架构评审 | ⏳ 待执行 | `reports/architect_review.md` |
| 01 | developer | 代码审查 | ⏳ 待执行 | `reports/developer_review.md` |
| 02 | tester | 测试用例设计 | ⏳ 待执行 | `reports/test_plan.md` |
| 03 | writer | 文档规划 | ⏳ 待执行 | `reports/doc_plan.md` |
| 04 | ui | UI 审查 | ⏳ 待执行 | `reports/ui_review.md` |

## 🚀 执行方式

### 方式 1：通过 CLI 调用（推荐）

```bash
# 调用 architect
openclaw sessions spawn --agent architect \
  --task-file TASKS/00_ARCHITECT_REVIEW.md \
  --model bailian/qwen3-max-2026-01-23

# 调用 developer
openclaw sessions spawn --agent developer \
  --task-file TASKS/01_DEVELOPER_REVIEW.md \
  --model bailian/qwen3-coder-plus

# 调用 tester
openclaw sessions spawn --agent tester \
  --task-file TASKS/02_TESTER_REVIEW.md \
  --model bailian/qwen3.5-plus

# 调用 writer
openclaw sessions spawn --agent writer \
  --task-file TASKS/03_WRITER_REVIEW.md \
  --model bailian/MiniMax-M2.5

# 调用 ui
openclaw sessions spawn --agent ui \
  --task-file TASKS/04_UI_REVIEW.md \
  --model bailian/qwen3-coder-plus
```

### 方式 2：由 main Agent 执行

如果无法直接调用子 Agent，可以由 main Agent（公司小龙虾）代为执行各 Agent 的任务。

## 📁 文件结构

```
TASKS/
├── README.md                    # 本文件 - 任务总览
├── MAIN_COORDINATOR.md          # 主控 Agent 协调指南
├── 00_ARCHITECT_REVIEW.md       # Architect 任务说明
├── 01_DEVELOPER_REVIEW.md       # Developer 任务说明
├── 02_TESTER_REVIEW.md          # Tester 任务说明
├── 03_WRITER_REVIEW.md          # Writer 任务说明
└── 04_UI_REVIEW.md              # UI 任务说明

reports/  # 各 Agent 输出报告（待创建）
├── architect_review.md
├── developer_review.md
├── test_plan.md
├── doc_plan.md
└── ui_review.md
```

## 📊 进度追踪

执行以下命令查看进度：

```bash
# 查看活跃会话
openclaw sessions list --active 60

# 查看特定 Agent 的会话
openclaw sessions list --agent architect

# 查看所有 Agent 的会话
openclaw sessions list --all-agents
```

## 🎯 下一步

1. 各 Agent 阅读项目文档和代码
2. 输出各自的评审报告
3. main Agent 汇总报告并向用户汇报
4. 进入问题修复和功能迭代阶段

---

*维护者：main Agent (公司小龙虾 🦞)*  
*更新时间：2026-03-03*
