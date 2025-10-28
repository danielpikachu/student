import streamlit as st
from datetime import date, timedelta

def render_calendar(is_admin):
    st.subheader("📅 日历管理")
    st.write("查看和管理学生会活动安排")
    st.divider()

    current_year, current_month = st.session_state.current_month

    # 月份导航
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("◀ 上月"):
            new_month = current_month - 1
            new_year = current_year
            if new_month < 1:
                new_month = 12
                new_year -= 1
            st.session_state.current_month = (new_year, new_month)
            st.rerun()  # 刷新以更新日历

    with col_title:
        month_name = date(current_year, current_month, 1).strftime("%Y年%m月")
        st.write(f"### {month_name}")

    with col_next:
        if st.button("下月 ▶"):
            new_month = current_month + 1
            new_year = current_year
            if new_month > 12:
                new_month = 1
                new_year += 1
            st.session_state.current_month = (new_year, new_month)
            st.rerun()  # 刷新以更新日历

    # 生成日历日期
    def get_month_days(year, month):
        first_day = date(year, month, 1)
        last_day = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
        start_day = first_day - timedelta(days=first_day.weekday())  # 周一为起始
        return [start_day + timedelta(days=i) for i in range(42)], first_day.month

    calendar_days, current_month_num = get_month_days(current_year, current_month)

    # 日历表头（周一到周日）
    headers = ["一", "二", "三", "四", "五", "六", "日"]
    for col, header in zip(st.columns(7), headers):
        if header in ["六", "日"]:
            col.markdown(f"**<span style='color: #ff4b4b'>{header}</span>**", unsafe_allow_html=True)
        else:
            col.markdown(f"**{header}**")

    # 渲染日历网格
    for i in range(6):
        cols = st.columns(7)
        for j in range(7):
            day = calendar_days[i*7 + j]
            day_str = day.strftime("%Y-%m-%d")
            is_current_month = day.month == current_month_num
            is_weekend = day.weekday() >= 5

            # 样式设置
            style = "padding: 8px; border-radius: 4px; margin: 2px; cursor: pointer;"
            if not is_current_month:
                style += "background: #f0f0f0; color: #888;"
            if day == date.today():
                style += "background: #e6f7ff; border: 2px solid #1890ff;"
            if is_weekend and is_current_month:
                style += "color: #ff4b4b;"
            if day == st.session_state.selected_date:
                style += "border: 2px solid #22c55e;"

            with cols[j]:
                # 点击日期选中
                if st.button(str(day.day), key=f"day_{day_str}", use_container_width=True):
                    st.session_state.selected_date = day
                    st.rerun()  # 刷新以高亮选中日期

                # 显示事件
                if day_str in st.session_state.calendar_events:
                    event = st.session_state.calendar_events[day_str]
                    st.markdown(f"<small>{event}</small>", unsafe_allow_html=True)

    # 管理员事件管理
    if is_admin:
        with st.expander("🔧 管理活动（仅管理员）", expanded=False):
            event_date = st.date_input("活动日期", st.session_state.selected_date)
            event_date_str = event_date.strftime("%Y-%m-%d")
            event_desc = st.text_input(
                "活动描述",
                st.session_state.calendar_events.get(event_date_str, "")
            )

            col_save, col_del = st.columns(2)
            with col_save:
                if st.button("保存活动"):
                    st.session_state.calendar_events[event_date_str] = event_desc
                    st.success("活动保存成功")
            with col_del:
                if st.button("删除活动", type="secondary") and event_date_str in st.session_state.calendar_events:
                    del st.session_state.calendar_events[event_date_str]
                    st.success("活动已删除")
