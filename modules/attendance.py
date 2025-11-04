import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态（确保使用唯一ID）
    if 'members' not in st.session_state:
        st.session_state.members = []  # 格式: [{"id": int, "name": str}, ...]
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 格式: [{"id": int, "name": str}, ...]
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # 格式: {(member_id, meeting_id): bool, ...}

    # 样式设置
    st.markdown("""
        <style>
            .scrollable-table {
                max-height: 300px;
                overflow-y: auto;
                overflow-x: auto;
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .table-row {
                display: flex;
                border-bottom: 1px solid #ddd;
            }
            .table-header {
                font-weight: bold;
                background-color: #f5f5f5;
            }
            .table-cell {
                flex: 1;
                padding: 10px;
                border-right: 1px solid #ddd;
                min-width: 120px;
                display: flex;
                align-items: center;
            }
            .table-cell:last-child {
                border-right: none;
            }
            .checkbox-container {
                width: 100%;
                display: flex;
                justify-content: center;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("Meeting Attendance Records")

    # 显示表格区域（导入成员后立即显示）
    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        # 检查是否有成员（无论是否有会议都显示表格结构）
        if st.session_state.members:
            # 表格列数：成员名列 + 会议列 + 出勤率列
            col_count = len(st.session_state.meetings) + 2
            
            # 表格头部
            header_cols = st.columns(col_count)
            with header_cols[0]:
                st.markdown('<div class="table-cell table-header">Member Name</div>', unsafe_allow_html=True)
            
            # 会议列标题
            for i, meeting in enumerate(st.session_state.meetings):
                with header_cols[i+1]:
                    st.markdown(f'<div class="table-cell table-header">{meeting["name"]}</div>', unsafe_allow_html=True)
            
            # 出勤率列标题
            with header_cols[-1]:
                st.markdown('<div class="table-cell table-header">Attendance Rates</div>', unsafe_allow_html=True)

            # 表格内容（所有成员都会显示）
            for member in st.session_state.members:
                row_cols = st.columns(col_count)
                attended_count = 0

                # 成员姓名
                with row_cols[0]:
                    st.markdown(f'<div class="table-cell">{member["name"]}</div>', unsafe_allow_html=True)

                # 会议出勤复选框（添加新会议时自动新增列）
                for i, meeting in enumerate(st.session_state.meetings):
                    key = f"att_{member['id']}_{meeting['id']}"
                    current_state = st.session_state.attendance.get((member['id'], meeting['id']), False)
                    
                    with row_cols[i+1]:
                        st.markdown('<div class="table-cell checkbox-container">', unsafe_allow_html=True)
                        new_state = st.checkbox(
                            label="",
                            value=current_state,
                            key=key,
                            label_visibility="collapsed"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 更新出勤状态
                        st.session_state.attendance[(member['id'], meeting['id'])] = new_state
                        if new_state:
                            attended_count += 1

                # 计算出勤率
                total_meetings = len(st.session_state.meetings)
                if total_meetings == 0:
                    rate = "N/A"
                else:
                    rate = f"{(attended_count / total_meetings * 100):.1f}%"
                
                with row_cols[-1]:
                    st.markdown(f'<div class="table-cell">{rate}</div>', unsafe_allow_html=True)

        else:
            st.info("请先导入成员以显示表格")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 管理功能区域
    st.header("Attendance Management Tools")

    # 1. 导入成员（导入后立即显示完整表格）
    with st.container():
        st.subheader("Import Members")
        col_import, col_info = st.columns([1, 2])
        with col_import:
            if st.button("Import from members.xlsx", key="import_btn"):
                try:
                    df = pd.read_excel("members.xlsx")
                    first_col = df.columns[0]
                    # 提取所有非空成员名（修复只显示最后一个的问题）
                    new_members = [str(name).strip() for name in df[first_col].dropna().unique() if str(name).strip()]
                    
                    if new_members:
                        # 清空现有成员（可选：如果需要保留现有成员可删除此行）
                        # st.session_state.members = []
                        
                        added = 0
                        for name in new_members:
                            # 避免重复添加
                            if not any(m["name"] == name for m in st.session_state.members):
                                st.session_state.members.append({
                                    "id": len(st.session_state.members) + 1,
                                    "name": name
                                })
                                added += 1
                        st.success(f"成功导入 {added} 个成员（来自 {first_col} 列）")
                    else:
                        st.warning("未在表格中找到有效成员")
                        
                except FileNotFoundError:
                    st.error("未找到 'members.xlsx' 文件，请确保文件存在")
                except Exception as e:
                    st.error(f"导入失败: {str(e)}")
        
        with col_info:
            st.info("请确保Excel文件与程序在同一目录，第一列包含成员姓名")

    # 2. 添加会议（添加后自动新增列）
    with st.container():
        st.subheader("Add Meeting")
        meeting_name = st.text_input("会议名称", placeholder="例如：周例会 2023-10-01", key="meeting_input")
        if st.button("添加会议", key="add_btn"):
            if not meeting_name.strip():
                st.error("请输入会议名称")
            elif any(m["name"] == meeting_name.strip() for m in st.session_state.meetings):
                st.error("该会议已存在")
            else:
                # 添加新会议（会自动在表格中生成新列）
                st.session_state.meetings.append({
                    "id": len(st.session_state.meetings) + 1,
                    "name": meeting_name.strip()
                })
                st.success(f"已添加会议: {meeting_name.strip()}")
                # 刷新页面以立即显示新列
                st.experimental_rerun()

if __name__ == "__main__":
    render_attendance()
