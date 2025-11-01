import streamlit as st

def render_calendar(gsheet_handler, sheet_name, data_key):
    """
    日历模块渲染函数
    :param gsheet_handler: GoogleSheetHandler实例，用于读写数据
    :param sheet_name: 对应Google Sheet分表名
    :param data_key: 会话状态中存储数据的键名
    """
    st.header("📅 日程管理")
    
    # 从会话状态获取数据（初始化时已从Google Sheet加载）
    calendar_data = st.session_state[data_key]
    
    # 显示现有数据
    st.subheader("现有日程")
    if calendar_data:
        st.dataframe(calendar_data)
    else:
        st.info("暂无日程数据，可添加新日程")
    
    # 新增日程表单
    st.subheader("添加新日程")
    with st.form(key="calendar_form"):
        date = st.date_input("日期")
        event = st.text_input("事件名称")
        person_in_charge = st.text_input("负责人")  # 修正变量名
        submit = st.form_submit_button("保存")
        
        if submit:
            # 新增数据到本地会话状态
            new_event = [str(date), event, person_in_charge]  # 同步修正
            st.session_state[data_key].append(new_event)
            
            # 同步到Google Sheet
            if gsheet_handler.save_data(sheet_name, st.session_state[data_key]):
                st.success("日程已保存并同步到云端！")
            else:
                st.success("日程已保存（本地模式）")
