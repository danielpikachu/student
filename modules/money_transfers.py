# 替换原有CSS部分，其他代码不变
st.markdown("""
<style>
    /* 核心滚动容器样式（加强优先级） */
    .scrollable-container {
        max-height: 50px !important;  /* 强制生效 */
        overflow-y: auto !important;  /* 强制垂直滚动 */
        padding: 10px !important;
        margin: 10px 0 !important;
        border: 1px solid #eee !important;  /* 增加边框，方便观察容器范围 */
    }
    
    /* 彻底清除内部元素的默认边距 */
    .scrollable-container * {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;  /* 压缩行高 */
    }
    
    /* 缩小字体和行高 */
    .small-text {
        font-size: 0.7rem !important;
        line-height: 1 !important;
    }
    
    /* 压缩表格行间距 */
    .st-emotion-cache-16txtl3 {
        padding-top: 0.05rem !important;
        padding-bottom: 0.05rem !important;
    }
    
    /* 压缩分隔线 */
    hr {
        margin: 0.05rem 0 !important;
        height: 1px !important;
    }
    
    /* 按钮压缩 */
    .stButton button {
        padding: 0.1rem 0.2rem !important;
        font-size: 0.6rem !important;
        height: auto !important;
    }
    
    /* 滚动条强制显示（调试用，可保留） */
    .scrollable-container::-webkit-scrollbar {
        width: 6px !important;
        display: block !important;
    }
    .scrollable-container::-webkit-scrollbar-track {
        background: #f1f1f1 !important;
    }
    .scrollable-container::-webkit-scrollbar-thumb {
        background: #888 !important;
    }
</style>
""", unsafe_allow_html=True)
