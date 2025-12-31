import streamlit as st

# --- 1. 配置與資料 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 固定轉換
LOCAL_FIX = {
    "視頻": "影片", "質量": "品質", "軟件": "軟體", "硬件": "硬體",
    "牛逼": "厲害", "立馬": "立刻", "特好": "很好"
}

# 歧義辨析 (改成更直覺的結構)
LOCAL_OPTIONS = {
    "土豆": {
        "cn": {"to": "馬鈴薯", "tag": "🇨🇳 中國語境 (Potato)"},
        "tw": {"to": "花生", "tag": "🇹🇼 台灣本土 (Peanut)"}
    },
    "窩心": {
        "cn": {"to": "貼心", "tag": "🇨🇳 中國語境 (暖心)"},
        "tw": {"to": "憋屈", "tag": "🇹🇼 傳統語境 (受氣)"}
    }
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def run_analysis():
    st.session_state.current_text = st.session_state.u_input
    st.session_state.is_analyzed = True

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"已轉換為：{new}")

# --- 2. UI 介面 ---
st.title("📱 語感守護者：直覺修正介面")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    st.text_area("測試文字：", height=150, value="我想吃土豆，順便看看視頻。", key="u_input")
    st.button("🚀 執行偵測", on_click=run_analysis, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.info("**修正後的結果：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 行動端 UI 模擬")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            st.markdown("<p style='text-align:center; color:gray;'>建議修正清單</p>", unsafe_allow_html=True)
            
            curr_text = st.session_state.current_text
            
            # A. 歧義詞：採用並排按鈕設計
            for old, v in LOCAL_OPTIONS.items():
                if old in curr_text:
                    st.markdown(f"**📍 偵測到多義詞：`{old}`**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.button(f"{v['cn']['tag']}\n\n替換為：{v['cn']['to']}", 
                                  key=f"cn_{old}", on_click=apply_change, args=(old, v['cn']['to']), use_container_width=True)
                    with col_b:
                        st.button(f"{v['tw']['tag']}\n\n替換為：{v['tw']['to']}", 
                                  key=f"tw_{old}", on_click=apply_change, args=(old, v['tw']['to']), use_container_width=True)
                    st.divider()
            
            # B. 固定詞：採用單行氣泡設計
            for old, new in LOCAL_FIX.items():
                if old in curr_text:
                    st.button(f"📘 將「{old}」修正為「{new}」", key=f"fix_{old}", 
                              on_click=apply_change, args=(old, new), use_container_width=True)
        else:
            st.info("👋 請輸入文字後點擊偵測。")
