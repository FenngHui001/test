#!/usr/bin/env python3
"""
小学托管班菜单生成器 - Streamlit 主程序
"""
import sys
from pathlib import Path
from datetime import datetime
from io import BytesIO

import streamlit as st
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from scraper import load_recipes
from menu_generator import MenuGenerator, MenuConfig, MealConfig


# 页面配置
st.set_page_config(
    page_title="小学托管班菜单生成器",
    page_icon="🍱",
    layout="wide"
)

# 标题
st.title("🍱 小学托管班菜单生成器")
st.markdown("---")


@st.cache_data
def get_recipes():
    """加载菜谱数据"""
    return load_recipes()


def create_config_from_ui() -> MenuConfig:
    """从 UI 创建配置"""
    config = MenuConfig()

    # 早餐配置
    config.breakfast.enabled = st.session_state.get("breakfast_enabled", True)

    # 午餐配置
    config.lunch.enabled = st.session_state.get("lunch_enabled", True)
    config.lunch.meat_count = st.session_state.get("lunch_meat", 2)
    config.lunch.veg_count = st.session_state.get("lunch_veg", 2)
    config.lunch.cold_count = st.session_state.get("lunch_cold", 1)
    config.lunch.soup_count = st.session_state.get("lunch_soup", 1)

    # 晚餐配置
    config.dinner.enabled = st.session_state.get("dinner_enabled", True)
    config.dinner.meat_count = st.session_state.get("dinner_meat", 1)
    config.dinner.veg_count = st.session_state.get("dinner_veg", 2)
    config.dinner.soup_count = st.session_state.get("dinner_soup", 1)
    config.dinner.noodle_count = st.session_state.get("dinner_noodle", 1)

    return config


def generate_menu():
    """生成菜单"""
    recipes = get_recipes()
    generator = MenuGenerator(recipes)
    config = create_config_from_ui()
    weekly_menu = generator.generate_weekly_menu(config)
    st.session_state["weekly_menu"] = weekly_menu
    st.session_state["ingredients"] = generator.get_all_ingredients(weekly_menu)


def get_dish_category_label(category):
    """获取菜品分类标签"""
    labels = {
        "荤菜": "🥩",
        "素菜": "🥬",
        "凉菜": "🥗",
        "汤类": "🍜",
        "面食": "🍝",
        "主食": "🍚",
        "早餐": "🍳"
    }
    return labels.get(category, "")


def display_menu_expanded():
    """显示展开式菜单（整周一个表格）"""
    if "weekly_menu" not in st.session_state:
        return

    weekly_menu = st.session_state["weekly_menu"]

    st.subheader("📅 本周菜单")

    table_data = []

    for daily in weekly_menu:
        day_label = f"{daily.day}\n{daily.date}"

        # 早餐
        if daily.breakfast:
            for i, dish in enumerate(daily.breakfast):
                ing_str = "、".join(dish.ingredients)
                table_data.append({
                    "日期": day_label if i == 0 else "",
                    "餐次": "早餐" if i == 0 else "",
                    "菜品": f"{get_dish_category_label(dish.category)} {dish.name}",
                    "所需食材": ing_str
                })

        # 午餐
        if daily.lunch:
            for i, dish in enumerate(daily.lunch):
                ing_str = "、".join(dish.ingredients)
                table_data.append({
                    "日期": day_label if (not daily.breakfast and i == 0) else "",
                    "餐次": "午餐" if i == 0 else "",
                    "菜品": f"{get_dish_category_label(dish.category)} {dish.name}",
                    "所需食材": ing_str
                })

        # 晚餐
        if daily.dinner:
            for i, dish in enumerate(daily.dinner):
                ing_str = "、".join(dish.ingredients)
                # 判断前面是否有早餐或午餐
                has_prev = (daily.breakfast and len(daily.breakfast) > 0) or (daily.lunch and len(daily.lunch) > 0)
                table_data.append({
                    "日期": day_label if (not has_prev and i == 0) else "",
                    "餐次": "晚餐" if i == 0 else "",
                    "菜品": f"{get_dish_category_label(dish.category)} {dish.name}",
                    "所需食材": ing_str
                })

    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "日期": st.column_config.TextColumn(width="medium"),
                "餐次": st.column_config.TextColumn(width="small"),
                "菜品": st.column_config.TextColumn(width="medium"),
                "所需食材": st.column_config.TextColumn(width="large"),
            }
        )


def export_to_word():
    """导出到 Word 文档（整周一个表格）"""
    if "weekly_menu" not in st.session_state:
        return

    weekly_menu = st.session_state["weekly_menu"]

    doc = Document()

    # 设置默认字体
    doc.styles['Normal'].font.name = '宋体'
    doc.styles['Normal']._element.rPr.rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia', '宋体')
    doc.styles['Normal'].font.size = Pt(11)

    # 标题
    title = doc.add_heading('小学托管班每周菜单', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 日期范围
    if weekly_menu:
        start_date = weekly_menu[0].date
        end_date = weekly_menu[-1].date
        date_para = doc.add_paragraph(f"日期范围：{start_date} 至 {end_date}")
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # 收集整周所有菜品
    all_rows = []
    day_merge_info = []
    meal_merge_info = []

    for daily in weekly_menu:
        day_label = f"{daily.day} ({daily.date})"
        day_start_row = len(all_rows) + 1  # +1 是表头

        # 早餐
        if daily.breakfast:
            meal_start_row = len(all_rows) + 1
            for i, dish in enumerate(daily.breakfast):
                all_rows.append((
                    day_label if i == 0 else "",
                    "早餐" if i == 0 else "",
                    dish.name,
                    "、".join(dish.ingredients)
                ))
            if len(daily.breakfast) > 1:
                meal_merge_info.append((meal_start_row, len(all_rows), 1))  # 餐次列是索引1
        elif daily.lunch or daily.dinner:
            # 如果没有早餐但有其他餐，第一天也要显示日期
            if not all_rows:
                pass

        # 午餐
        if daily.lunch:
            meal_start_row = len(all_rows) + 1
            for i, dish in enumerate(daily.lunch):
                show_day = (not daily.breakfast and i == 0)
                all_rows.append((
                    day_label if show_day else "",
                    "午餐" if i == 0 else "",
                    dish.name,
                    "、".join(dish.ingredients)
                ))
            if len(daily.lunch) > 1:
                meal_merge_info.append((meal_start_row, len(all_rows), 1))
        elif daily.dinner:
            if not all_rows:
                pass

        # 晚餐
        if daily.dinner:
            meal_start_row = len(all_rows) + 1
            has_prev = (daily.breakfast and len(daily.breakfast) > 0) or (daily.lunch and len(daily.lunch) > 0)
            for i, dish in enumerate(daily.dinner):
                show_day = (not has_prev and i == 0)
                all_rows.append((
                    day_label if show_day else "",
                    "晚餐" if i == 0 else "",
                    dish.name,
                    "、".join(dish.ingredients)
                ))
            if len(daily.dinner) > 1:
                meal_merge_info.append((meal_start_row, len(all_rows), 1))

        # 记录日期合并信息
        day_end_row = len(all_rows)
        if day_end_row > day_start_row:
            day_merge_info.append((day_start_row, day_end_row, 0))

    if all_rows:
        # 创建表格
        table = doc.add_table(rows=len(all_rows) + 1, cols=4)
        table.style = 'Table Grid'
        table.autofit = True

        # 设置列宽
        for row in table.rows:
            row.cells[0].width = Cm(3)
            row.cells[1].width = Cm(2)
            row.cells[2].width = Cm(5)
            row.cells[3].width = Cm(9)

        # 表头
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = '日期'
        hdr_cells[1].text = '餐次'
        hdr_cells[2].text = '菜品'
        hdr_cells[3].text = '所需食材'

        # 设置表头样式
        for cell in hdr_cells:
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].runs[0].font.size = Pt(11)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 填充数据
        for i, (day, meal, dish, ing) in enumerate(all_rows):
            row_cells = table.rows[i + 1].cells
            row_cells[0].text = day
            row_cells[1].text = meal
            row_cells[2].text = dish
            row_cells[3].text = ing

            for cell in row_cells:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in cell.paragraphs[0].runs:
                    run.font.size = Pt(10)

        # 合并日期单元格
        for start, end, col_idx in day_merge_info:
            if end > start:
                table.rows[start].cells[col_idx].merge(table.rows[end - 1].cells[col_idx])
                merged = table.rows[start].cells[col_idx]
                merged.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 合并餐次单元格
        for start, end, col_idx in meal_merge_info:
            if end > start:
                table.rows[start].cells[col_idx].merge(table.rows[end - 1].cells[col_idx])
                merged = table.rows[start].cells[col_idx]
                merged.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 保存到内存
    output = BytesIO()
    doc.save(output)
    output.seek(0)

    st.download_button(
        label="📥 下载 Word 文档",
        data=output,
        file_name=f"每周菜单_{datetime.now().strftime('%Y%m%d')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


def export_to_excel():
    """导出到 Excel（整周一个表格）"""
    if "weekly_menu" not in st.session_state:
        return

    weekly_menu = st.session_state["weekly_menu"]

    output = BytesIO()

    table_data = []

    for daily in weekly_menu:
        day_label = f"{daily.day} ({daily.date})"

        # 早餐
        if daily.breakfast:
            for i, dish in enumerate(daily.breakfast):
                table_data.append({
                    "日期": day_label if i == 0 else "",
                    "餐次": "早餐" if i == 0 else "",
                    "菜品": dish.name,
                    "所需食材": "、".join(dish.ingredients)
                })

        # 午餐
        if daily.lunch:
            for i, dish in enumerate(daily.lunch):
                has_prev = (daily.breakfast and len(daily.breakfast) > 0)
                table_data.append({
                    "日期": day_label if (not has_prev and i == 0) else "",
                    "餐次": "午餐" if i == 0 else "",
                    "菜品": dish.name,
                    "所需食材": "、".join(dish.ingredients)
                })

        # 晚餐
        if daily.dinner:
            for i, dish in enumerate(daily.dinner):
                has_prev = (daily.breakfast and len(daily.breakfast) > 0) or (daily.lunch and len(daily.lunch) > 0)
                table_data.append({
                    "日期": day_label if (not has_prev and i == 0) else "",
                    "餐次": "晚餐" if i == 0 else "",
                    "菜品": dish.name,
                    "所需食材": "、".join(dish.ingredients)
                })

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if table_data:
            df = pd.DataFrame(table_data)
            df.to_excel(writer, sheet_name="本周菜单", index=False)

    output.seek(0)

    st.download_button(
        label="📥 下载 Excel 文件",
        data=output,
        file_name=f"每周菜单_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ===== 侧边栏配置 =====
st.sidebar.header("⚙️ 菜单配置")

# 餐次选择
st.sidebar.subheader("选择餐次")
st.session_state["breakfast_enabled"] = st.sidebar.checkbox("早餐", value=True)
st.session_state["lunch_enabled"] = st.sidebar.checkbox("午餐", value=True)
st.session_state["dinner_enabled"] = st.sidebar.checkbox("晚餐", value=True)

st.sidebar.markdown("---")

# 午餐配置
if st.session_state.get("lunch_enabled", True):
    st.sidebar.subheader("午餐配置")
    st.session_state["lunch_meat"] = st.sidebar.number_input("荤菜数量", min_value=0, max_value=5, value=2)
    st.session_state["lunch_veg"] = st.sidebar.number_input("素菜数量", min_value=0, max_value=5, value=2)
    st.session_state["lunch_cold"] = st.sidebar.number_input("凉菜数量", min_value=0, max_value=5, value=1)
    st.session_state["lunch_soup"] = st.sidebar.number_input("汤类数量", min_value=0, max_value=5, value=1)

    st.sidebar.markdown("---")

# 晚餐配置
if st.session_state.get("dinner_enabled", True):
    st.sidebar.subheader("晚餐配置")
    st.session_state["dinner_meat"] = st.sidebar.number_input("荤菜数量", min_value=0, max_value=5, value=1, key="dinner_meat_key")
    st.session_state["dinner_veg"] = st.sidebar.number_input("素菜数量", min_value=0, max_value=5, value=2, key="dinner_veg_key")
    st.session_state["dinner_soup"] = st.sidebar.number_input("汤类数量", min_value=0, max_value=5, value=1, key="dinner_soup_key")
    st.session_state["dinner_noodle"] = st.sidebar.number_input("面食数量", min_value=0, max_value=5, value=1, key="dinner_noodle_key")

st.sidebar.markdown("---")

# 生成按钮
if st.sidebar.button("✨ 生成本周菜单", type="primary", use_container_width=True):
    with st.spinner("正在生成菜单..."):
        generate_menu()
    st.success("菜单生成成功！")


# ===== 主内容区域 =====
# 显示菜谱库状态
recipes = get_recipes()
if recipes:
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("荤菜", len(recipes.get("荤菜", [])))
    col2.metric("素菜", len(recipes.get("素菜", [])))
    col3.metric("凉菜", len(recipes.get("凉菜", [])))
    col4.metric("汤类", len(recipes.get("汤类", [])))
    col5.metric("面食", len(recipes.get("面食", [])))
    col6.metric("早餐", len(recipes.get("早餐", [])))

st.markdown("---")

# 显示菜单
if "weekly_menu" in st.session_state:
    display_menu_expanded()

    # 导出按钮
    st.subheader("📤 导出与分享")
    col1, col2 = st.columns(2)
    with col1:
        export_to_word()
    with col2:
        export_to_excel()

    # 分享提示
    st.info("💡 提示：点击上方按钮下载 Word 或 Excel 文件后，可通过微信、QQ 等方式分享给同事或家长！")

else:
    st.info("👈 请在左侧配置好菜单选项，然后点击「生成本周菜单」按钮！")


# 页脚
st.markdown("---")
st.caption("小学托管班菜单生成器 | 数据来源：内置菜谱库 + 下厨房")
