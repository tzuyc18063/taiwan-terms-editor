import streamlit as st
import pandas as pd

# 1. 核心語感轉換字典
TAIWAN_TERMS = {
    "視頻": "影片", "軟件": "軟體", "硬盤": "硬碟", "質量": "品質",
    "優化": "最佳化", "支持": "支援", "菜單": "選單", "激活": "啟用",
    "打印": "列印", "實時": "即時", "信號": "訊號", "信息": "訊息",
    "屏幕": "螢幕", "內存": "記憶體", "鼠標": "滑鼠", "充電寶": "行動電源",
    "網絡": "網路", "程序": "程式", "服務器": "伺服器", "硬體": "硬體"
}

# 頁面配置
st.set_page_config(page_title="台灣語感轉換器", layout="wide")

# 2. 修正後的 CSS (確保 unsafe_allow_html 為 True)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main { padding-top: 2rem; }
    .stTextArea textarea { font-size: 1.1rem !important; border-radius: 8px !important; border: 1px solid #e0e0e0 !important; }
    div.stButton > button { 
        width: 100%; 
        background-color: #007bff; 
        color: white; 
        border-radius: 5px; 
        height: 3em;
        font-weight: bold;
    }
    div.stButton > button:hover { border: 1px solid #0056b3; background-color: #0056b3; color: white; }
    </style>
""", unsafe_allow_html=True)

# 3. 側邊欄：顯示對照表
with st.sidebar:
    st.title("⚙️ 術語管理")
    st.write("目前採本地運作模式，不連接雲端資料庫。")
    st.divider()
    st.subheader("目前支援的轉換")
    df = pd.DataFrame(list(TAIWAN_TERMS.items()), columns=['大陸用語', '台灣在地語感'])
    st.dataframe(df, use_container_width=True, hide_index=True)

# 4. 主介面
st.title("🇹🇼 台灣語感 (Taiwanese Style) 轉換器")
st.write("將文字貼在左側，系統將自動套用台灣常用術語對照。")

col1, col2 = st.columns(2)

with col1:
    st.subheader("原始文字")
    input_text = st.text_area("請在此輸入內容...", placeholder="例如：這個視頻的質量優化得不錯...", height=400)

with col2:
    st.subheader("轉換結果")
    
    # 執行轉換邏輯
    output_text = input_text
    if input_text:
        for cn, tw in TAIWAN_TERMS.items():
            output_text = output_text.replace(cn, tw)
    
    st.text_area("自動轉換後：", value=output_text, height=400)

# 功能操作區
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])

if c1.button("✨ 執行語感優化"):
    st.toast("已完成語感轉換！")

if c2.button("🧹 清除全部內容"):
    st.rerun()

st.caption("版本說明：這是一個完全在本地運行的編輯器，不涉及雲端存取，速度最快且最穩定。")
