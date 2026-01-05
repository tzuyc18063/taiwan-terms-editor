import streamlit as st
import pandas as pd

# 1. 核心詞典：包含解釋與用法差異 (這就是你說的重點)
TERM_EXPLANATIONS = {
    "視頻": {
        "tw": "影片",
        "diff": "大陸稱『視頻』源於頻率信號；台灣習慣稱『影片』，延續電影片、底片的說法。",
        "example": "例：這個影片很有趣。"
    },
    "軟件": {
        "tw": "軟體",
        "diff": "台灣統一將 Software 譯為『軟體』，硬體則是 Hardware；大陸則使用『件』字。",
        "example": "例：這套軟體很好用。"
    },
    "質量": {
        "tw": "品質 / 質感",
        "diff": "大陸『質量』兼具物理質量與 Quality 的意思；台灣在形容產品好壞時必用『品質』。",
        "example": "例：這件衣服的品質很好。"
    },
    "優化": {
        "tw": "最佳化",
        "diff": "大陸泛指所有改善；台灣在電腦科學領域常用『最佳化』，生活語境則說『改善』或『提升』。",
        "example": "例：程式碼需要最佳化。"
    },
    "信息": {
        "tw": "訊息 / 資訊",
        "diff": "大陸將 Message 和 Information 統稱為信息；台灣區分得很清楚，Message 是訊息，Data 是資訊。",
        "example": "例：我收到一則訊息。"
    }
}

# 2. 頁面美化
st.set_page_config(page_title="台灣語感翻譯專家", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .explanation-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .tw-term { color: #007bff; font-weight: bold; font-size: 1.2em; }
    .diff-text { color: #555; font-size: 0.95em; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# 3. 主介面
st.title("🇹🇼 台灣語感專家：用語轉換與用法解釋")
st.write("不只是翻譯，更告訴你兩岸用法的差異點。")

# 4. 側邊欄：互動式詞典按鈕
with st.sidebar:
    st.header("📚 術語百科")
    st.write("點擊下方術語查看差異說明：")
    for cn in TERM_EXPLANATIONS.keys():
        if st.button(f"🔍 {cn} vs {TERM_EXPLANATIONS[cn]['tw']}"):
            st.session_state.selected_term = cn

# 5. 文字轉換區
col1, col2 = st.columns(2)

with col1:
    st.subheader("輸入原始內容")
    input_text = st.text_area("在此輸入...", placeholder="請輸入包含大陸用語的內容...", height=300)

with col2:
    st.subheader("轉換結果")
    output_text = input_text
    found_terms = []
    if input_text:
        for cn, info in TERM_EXPLANATIONS.items():
            if cn in input_text:
                output_text = output_text.replace(cn, f"**{info['tw']}**")
                found_terms.append(cn)
    
    st.markdown(f'<div style="background:white; padding:15px; border-radius:8px; border:1px solid #ddd; min-height:300px;">{output_text}</div>', unsafe_allow_html=True)

# 6. 動態解釋區：根據點擊或偵測到的詞彙顯示
st.divider()
st.subheader("💡 用法差異詳解")

# 如果有點選側邊欄或偵測到文字中有關鍵字
term_to_show = st.session_state.get('selected_term')

if term_to_show:
    info = TERM_EXPLANATIONS[term_to_show]
    st.markdown(f"""
    <div class="explanation-card">
        <span style="font-size:1.5em;">🇨🇳 {term_to_show} ➔ <span class="tw-term">🇹🇼 {info['tw']}</span></span><br><br>
        <p class="diff-text"><b>【差異解釋】</b><br>{info['diff']}</p>
        <p style="color: green; font-style: italic;">{info['example']}</p>
    </div>
    """, unsafe_allow_html=True)
elif not found_terms:
    st.info("在上方輸入文字或點擊左側術語，這裡會顯示詳細的用法差異解釋。")
else:
    st.success(f"偵測到以下術語：{', '.join(found_terms)}。點擊左側側邊欄可查看詳細解釋。")

# 功能鍵
if st.button("🧹 清除畫面"):
    st.session_state.selected_term = None
    st.rerun()
