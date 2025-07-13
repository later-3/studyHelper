# StudyHelper v2.0 - 智能学习助手

一个基于AI的智能学习助手系统，支持多角色用户管理和数据分析。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Streamlit

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
# 运行主应用（推荐）
streamlit run apps/app_v2.py

# 运行旧版本应用
streamlit run apps/app.py
```

## 📁 项目结构

```
studyhelper-demo-final/
├── apps/                    # 应用入口文件
│   ├── app.py              # 原始应用
│   └── app_v2.py           # 升级版应用（推荐）
├── core/                    # 核心业务逻辑
│   ├── question_manager.py  # 题目管理
│   ├── history_management.py # 历史记录管理
│   ├── user_management.py   # 用户管理（旧版）
│   ├── user_management_v2.py # 用户管理（新版）
│   └── logger_config.py     # 日志配置
├── services/                # 服务层
│   ├── data_service.py      # 数据服务
│   ├── storage_service.py   # 存储服务
│   ├── ocr_service.py       # OCR服务
│   └── llm_service.py       # LLM服务
├── components/              # UI组件
│   ├── student_dashboard.py     # 学生仪表盘
│   ├── teacher_dashboard.py     # 教师仪表盘
│   ├── grade_manager_dashboard.py # 年级主任仪表盘
│   ├── principal_dashboard.py   # 校长仪表盘
│   └── ui_components.py         # 通用UI组件
├── tests/                   # 单元测试
├── scripts/                 # 测试和调试脚本
├── docs/                    # 文档
├── data/                    # 数据文件
├── assets/                  # 静态资源
├── llm/                     # LLM相关
├── ocr/                     # OCR相关
├── recommender/             # 推荐系统
├── logs/                    # 日志文件
├── devLog/                  # 开发日志
├── arch/                    # 架构文档
├── studyhelper/             # 虚拟环境
├── requirements.txt         # 依赖列表
└── .gitignore              # Git忽略文件
```

## 👥 用户角色

系统支持四种用户角色：

1. **学生 (Student)** - 查看个人答题历史和统计
2. **教师 (Teacher)** - 查看所教班级学生表现
3. **年级主任 (Grade Manager)** - 查看年级整体表现
4. **校长 (Principal)** - 查看全校整体表现

## 🎯 主要功能

- **智能答题分析** - AI驱动的题目识别和分析
- **角色化仪表盘** - 不同角色看到不同的数据视图
- **历史记录管理** - 完整的答题历史追踪
- **数据统计分析** - 多维度数据分析和可视化
- **用户权限管理** - 基于角色的访问控制

## 🔧 开发说明

### 添加新功能
1. 在 `core/` 中添加业务逻辑
2. 在 `services/` 中添加服务层
3. 在 `components/` 中添加UI组件
4. 在 `tests/` 中添加测试用例

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_student_dashboard.py
```

### 调试脚本
```bash
# 运行调试脚本
python scripts/test_data_service.py
```

## 📝 版本历史

- **v2.0** - 角色化用户体验升级版
  - 新增多角色仪表盘
  - 优化UI/UX设计
  - 完善错误处理
  - 重构代码结构

- **v1.0** - 基础版本
  - 基础答题功能
  - AI分析集成
  - 简单用户管理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。 