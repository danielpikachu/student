# 修改同步到Sheet的函数，确保完全一致
def sync_interface_to_sheet():
    if not attendance_sheet or not sheet_handler:
        return
        
    # 确保表头一致
    ensure_sheet_structure()
    
    try:
        # 1. 准备与界面完全相同的数据
        sheet_data = []
        for member in st.session_state.att_members:
            row = [member["name"]]  # 成员名
            # 各会议出勤状态（与界面显示一致：✓/✗）
            for meeting in st.session_state.att_meetings:
                row.append("✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗")
            # 出勤率（与界面显示一致：百分比）
            attended_count = sum(1 for m in st.session_state.att_meetings 
                               if st.session_state.att_records.get((member["id"], m["id"]), False))
            total_meetings = len(st.session_state.att_meetings)
            row.append(f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%")
            sheet_data.append(row)
        
        # 2. 清除工作表中所有现有数据（包括格式）
        attendance_sheet.clear()
        
        # 3. 重新写入表头
        interface_columns = ["Member Name"] + [m["name"] for m in st.session_state.att_meetings] + ["Attendance Rates"]
        attendance_sheet.append_row(interface_columns)
        attendance_sheet.format("1:1", {"textFormat": {"bold": True}})
        
        # 4. 写入所有数据行
        if sheet_data:
            attendance_sheet.append_rows(sheet_data)
            
            # 5. 设置出勤率列格式为百分比
            if st.session_state.att_meetings:
                rate_col = len(st.session_state.att_meetings) + 2  # 出勤率列索引
                attendance_sheet.format(f"{chr(64 + rate_col)}2:{chr(64 + rate_col)}{len(sheet_data) + 1}", 
                                      {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}})
            
            return True
        return False
        
    except HttpError as e:
        if e.resp.status == 429:
            st.warning("同步频率超限，请稍后再试")
        else:
            st.error(f"同步到Google Sheet失败: {str(e)}")
        return False
    except Exception as e:
        st.error(f"同步失败: {str(e)}")
        return False
