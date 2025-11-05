import streamlit as st

def render_money_transfers(namespace):
    """转账模块渲染函数，使用命名空间隔离状态"""
    st.header("资金转账管理")
    
    # 生成带命名空间的key
    def get_key(name):
        return f"{namespace}_{name}"
    
    # 初始化当前模块的会话状态（如果需要）
    if "initialized" not in st.session_state[namespace]:
        st.session_state[namespace]["initialized"] = True
    
    # 转账表单
    with st.expander("新增转账记录", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            amount = st.number_input(
                "转账金额", 
                min_value=0.01, 
                step=0.01, 
                key=get_key("amount")
            )
        with col2:
            recipient = st.text_input(
                "接收方", 
                key=get_key("recipient")
            )
        with col3:
            category = st.selectbox(
                "转账类别", 
                st.session_state[namespace]["categories"],
                key=get_key("category")
            )
        
        description = st.text_area(
            "转账说明", 
            key=get_key("description")
        )
        
        if st.button("提交转账", key=get_key("submit")):
            new_transfer = {
                "amount": amount,
                "recipient": recipient,
                "category": category,
                "description": description,
                "status": "pending"
            }
            st.session_state[namespace]["records"].append(new_transfer)
            st.session_state[namespace]["pending"].append(new_transfer)
            st.success("转账记录已添加")
    
    # 展示转账记录
    st.subheader("转账记录")
    if st.session_state[namespace]["records"]:
        for i, transfer in enumerate(st.session_state[namespace]["records"]):
            with st.container():
                st.write(f"**编号**: {i+1}")
                st.write(f"**金额**: ¥{transfer['amount']}")
                st.write(f"**接收方**: {transfer['recipient']}")
                st.write(f"**状态**: {transfer['status']}")
                st.divider()
    else:
        st.info("暂无转账记录")
