# 修改calendar.py中渲染日历网格的部分
# 绘制日历网格
current_day = 1
while current_day <= days_in_month:
    day_cols = st.columns(7)
    for col_idx in range(7):
        with day_cols[col_idx]:
            if current_day == 1 and col_idx < first_weekday:
                st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
            else:
                if current_day > days_in_month:
                    st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                else:
                    current_date = datetime(year, month, current_day)
                    date_key = current_date.strftime("%Y-%m-%d")
                    is_today = (current_date.date() == datetime.today().date())
                    has_event = date_key in date_events

                    # 卡片样式
                    day_classes = "calendar-day"
                    if is_today:
                        day_classes += " calendar-day-today"
                    if has_event:
                        day_classes += " calendar-day-has-event"

                    # 事件文本 - 优化显示逻辑
                    event_text = ""
                    if has_event:
                        # 限制显示长度，过长文本显示省略号
                        desc = date_events[date_key]
                        display_desc = desc[:30] + "..." if len(desc) > 30 else desc
                        event_text = f"<div class='event-text'>{display_desc}</div>"

                    # 渲染卡片
                    st.markdown(f"""
                    <div class='{day_classes}'>
                        <div class='day-number'>{current_day}</div>
                        {event_text}
                    </div>
                    """, unsafe_allow_html=True)
                    current_day += 1
