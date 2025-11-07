# modules/groups.py
import streamlit as st
from datetime import datetime
import uuid
import sys
import os
# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_groups():
    """渲染小组模块界面（gro_前缀命名空间）"""
    st.header("👥 Groups Management")
    st.markdown("---")
    
    # 初始化Google Sheets连接（参考money_transfers.py）
    sheet_handler = None
    groups_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        groups_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Groups"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")
    
    # 从Google Sheets同步数据（使用gro_records状态，参考转账模块）
    if groups_sheet and sheet_handler and (not st.session_state.get("gro_records")):
        try:
            all_data = groups_sheet.get_all_values()
            expected_headers = ["uuid", "name", "created_at", "description", "leader"]
            
            # 检查表头
            if not all_data or all_data[0] != expected_headers:
                groups_sheet.clear()
                groups_sheet.append_row(expected_headers)
                records = []
            else:
                # 处理数据（跳过表头）
                records = [
                    {
                        "uuid": row[0],
                        "name": row[1],
                        "created_at": datetime.strptime(row[2], "%Y-%m-%d").date(),
                        "description": row[3],
                        "leader": row[4]
                    } 
                    for row in all_data[1:] 
                    if row[0]  # 确保UUID不为空
                ]
            
            st.session_state.gro_records = records
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")
    
    # 初始化状态（确保有8个默认组，参考原有界面需求）
    if "gro_records" not in st.session_state:
        st.session_state.gro_records = [
            {"uuid": str(uuid.uuid4()), "name": "Group 1", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 1", "leader": "Leader 1"},
            {"uuid": str(uuid.uuid4()), "name": "Group 2", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 2", "leader": "Leader 2"},
            {"uuid": str(uuid.uuid4()), "name": "Group 3", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 3", "leader": "Leader 3"},
            {"uuid": str(uuid.uuid4()), "name": "Group 4", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 4", "leader": "Leader 4"},
            {"uuid": str(uuid.uuid4()), "name": "Group 5", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 5", "leader": "Leader 5"},
            {"uuid": str(uuid.uuid4()), "name": "Group 6", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 6", "leader": "Leader 6"},
            {"uuid": str(uuid.uuid4()), "name": "Group 7", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 7", "leader": "Leader 7"},
            {"uuid": str(uuid.uuid4()), "name": "Group 8", "created_at": datetime(2023, 9, 1).date(), "description": "Default group 8", "leader": "Leader 8"}
        ]
    
    # ---------------------- 小组列表展示（保持原有界面） ----------------------
    st.subheader("Group List")
    if not st.session_state.gro_records:
        st.info("No groups created yet")
    else:
        # 定义列宽比例（保持原有布局）
        col_widths = [0.3, 2.0, 1.5, 2.5, 1.5, 1.0]
        
        # 显示固定表头
        header_cols = st.columns(col_widths)
        with header_cols[0]:
            st.write("**#**")
        with header_cols[1]:
            st.write("**Group Name**")
        with header_cols[2]:
            st.write("**Created Date**")
        with header_cols[3]:
            st.write("**Description**")
        with header_cols[4]:
            st.write("**Leader**")
        with header_cols[5]:
            st.write("**Action**")
        
        st.markdown("---")
        
        # 滚动容器（保持原有高度）
        scroll_container = st.container(height=320)
        with scroll_container:
            # 遍历显示每个小组
            for idx, group in enumerate(st.session_state.gro_records, 1):
                unique_key = f"gro_delete_{idx}_{group['uuid']}"  # 唯一键命名规范
                cols = st.columns(col_widths)
                
                with cols[0]:
                    st.write(idx)
                with cols[1]:
                    st.write(group["name"])
                with cols[2]:
                    st.write(group["created_at"].strftime("%Y-%m-%d"))
                with cols[3]:
                    st.write(group["description"])
                with cols[4]:
                    st.write(group["leader"])
                with cols[5]:
                    # 删除按钮逻辑（参考转账模块）
                    if st.button(
                        "🗑️ Delete", 
                        key=unique_key,
                        use_container_width=True,
                        type="secondary"
                    ):
                        # 1. 删除本地状态数据
                        st.session_state.gro_records.pop(idx - 1)
                        
                        # 2. 同步删除Google Sheets记录
                        if groups_sheet and sheet_handler:
                            try:
                                cell = groups_sheet.find(group["uuid"])
                                if cell:
                                    groups_sheet.delete_rows(cell.row)
                                st.success(f"Group {idx} deleted successfully!")
                                st.rerun()  # 立即刷新界面
                            except Exception as e:
                                st.warning(f"同步删除失败: {str(e)}")
                
                st.markdown("---")
        
        # 原有统计展示
        st.markdown(f"""
        <div style='margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 8px;'>
            <strong>Total Groups: {len(st.session_state.gro_records)}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("=" * 50)
    
    # ---------------------- 新增小组（保持界面，修改逻辑） ----------------------
    st.subheader("Create New Group")
    col1, col2 = st.columns(2)
    
    with col1:
        group_name = st.text_input(
            "Group Name", 
            value=st.session_state.get("gro_new_name", ""),
            key="gro_input_name"
        ).strip()
        
        created_date = st.date_input(
            "Creation Date", 
            value=datetime.today(),
            key="gro_input_date"
        )
    
    with col2:
        description = st.text_input(
            "Description", 
            value="Group purpose and goals",
            key="gro_input_desc"
        ).strip()
        
        leader = st.text_input(
            "Group Leader", 
            value="",
            key="gro_input_leader"
        ).strip()
    
    # 创建小组按钮逻辑（参考转账模块）
    if st.button("Create Group", key="gro_btn_create", use_container_width=True, type="primary"):
        # 验证必填字段
        if not group_name or not leader:
            st.error("Group Name and Leader are required fields!")
            return
        
        # 1. 创建新小组记录
        new_group = {
            "uuid": str(uuid.uuid4()),  # 唯一标识
            "name": group_name,
            "created_at": created_date,
            "description": description,
            "leader": leader
        }
        
        # 2. 更新本地状态
        st.session_state.gro_records.append(new_group)
        
        # 3. 同步到Google Sheets
        if groups_sheet and sheet_handler:
            try:
                groups_sheet.append_row([
                    new_group["uuid"],
                    new_group["name"],
                    new_group["created_at"].strftime("%Y-%m-%d"),
                    new_group["description"],
                    new_group["leader"]
                ])
                st.success("Group created successfully!")
                st.rerun()  # 立即刷新界面
            except Exception as e:
                st.warning(f"同步到Google Sheets失败: {str(e)}")
