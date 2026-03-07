# 🍱 小学托管班菜单生成器

一个简单易用的每周菜单生成工具，专为小学托管班设计。

## 功能特点

- 📅 自动生成周一到周五的菜单
- 🍽️ 可选择生成早餐、午餐、晚餐
- ⚙️ 灵活配置各餐次的菜品数量（荤菜、素菜、凉菜、汤类、面食）
- 🛒 自动生成食材清单
- 📊 表格形式展示，清晰易读
- 📥 支持导出 Excel 文件，方便分享

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
streamlit run app.py
```

程序会自动在浏览器中打开。

## 使用说明

### 配置菜单

在左侧边栏配置：
1. 选择需要生成的餐次（早/午/晚）
2. 设置各餐次的菜品数量
3. 点击「生成本周菜单」

### 导出分享

- 点击「下载 Excel 文件」按钮导出菜单
- Excel 包含两张表：本周菜单、食材清单

### 更新菜谱库（可选）

如需从下厨房获取最新菜谱：

```bash
python scraper.py update
```

## 项目结构

```
menu-generator/
├── app.py              # Streamlit 主程序
├── menu_generator.py   # 菜单生成逻辑
├── scraper.py          # 下厨房爬虫
├── data/
│   └── recipes.json    # 菜谱数据库
├── requirements.txt    # 依赖包
└── README.md
```
