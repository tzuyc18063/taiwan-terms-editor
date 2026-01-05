import streamlit as st
import pandas as pd

# 1. 核心語感轉換字典 (擴展更多常用術語)
DEFAULT_TERMS = {
    "視頻": "影片", "軟件": "軟體", "硬盤": "硬碟", "質量": "品質",
    "優化": "最佳化", "支持": "支援", "菜單": "選單", "激活": "啟用",
    "打印": "列印", "實時": "即時", "信號": "訊號", "信息": "訊息",
    "屏幕": "螢幕", "內存": "記憶體", "鼠標": "滑鼠", "充電寶": "行動電源"
}

# 頁面配置：讓介面看起來更專業
st.set_page_config(page_title="台灣語感術語轉換器", layout="wide")

# 自定義 CSS：讓介面更顯白、乾淨
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stTextArea textarea { font-size: 16px !important; border-radius: 10px !important; }
    .stButton button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; }
    </style>
""", unsafe_allow_stdio=True)

# 2. 側邊欄：管理功能
with st.sidebar:
    st.header("⚙️ 設定與管理")
    st.info("目前模式：本地高速運行 (No Cloud)")
    
    st.subheader("術語對照表")
    # 將字典轉為 DataFrame 顯示，看起來更專業
    df = pd.DataFrame(list(DEFAULT_TERMS.items()), columns=['大陸術語', '台灣語感'])
    st.dataframe(df, height=400, use_container_width=True)

# 3. 主界面布局
st.title("🇹🇼 台灣語感 (Taiwanese Style) 轉換器")
st.caption("自動修正大陸用語，恢復台灣在地語感，適用於文案、報告與程式註解。")

col1, col2 = st.columns(2)

with col1:
    st.subheader("原始文字")
    input_text = st.text_area("在此輸入或貼上內容...", placeholder="例如：這個視頻的質量優化得很好...", height=350)

with col2:
    st.subheader("轉換結果")
    
    # 執行轉換邏輯
    output_text = input_text
    if input_text:
        for cn, tw in DEFAULT_TERMS.items():
            output_text = output_text.replace(cn, tw)
    
    st.text_area("自動轉換後的內容...", value=output_text, height=350, key="output")

# 4. 底部功能鍵
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])

if c1.button("✨ 一鍵優化語感"):
    st.toast("轉換完成！")

if c2.button("📋 複製結果"):
    st.write("請直接從右側文字框全選複製 (Ctrl+A / Ctrl+C)")

if c3.button("🧹 清空內容"):
    st.rerun()

# 頁尾資訊
st.caption("💡 提示：此版本不經過任何雲端 API，保護您的資料隱私且反應最快。")
