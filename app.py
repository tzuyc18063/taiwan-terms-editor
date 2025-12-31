import streamlit as st

# --- 1. 配置與百科資料 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 百科式資料結構
WIKI_DICT = {
    "土豆": {
        "title": "🥔 土豆 (Tǔ dòu)",
        "tw_meaning": "🥜 在台灣通常指「花生」 (Peanut)",
        "cn_meaning": "🍟 在中國是指「馬鈴薯」 (Potato)",
        "suggestion": "影片中若指洋芋片原料，台灣應稱「馬鈴薯」。"
    },
    "窩心": {
        "title": "❤️ 窩心 (Wō xīn)",
        "tw_meaning": "😣 在台灣傳統指「憋屈、心裡難受」",
        "cn_meaning": "🥰 在中國是指「貼心、暖心」",
        "suggestion": "若要表達溫暖，台灣建議用「貼心」。"
    }
}

# 固定直接轉換
LOCAL_FIX = {"視頻": "影片", "質量": "品質", "軟件": "軟體", "牛逼": "厲害"}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已為您修正為：{new}")

# --- 2. UI 介面 ---
st.title("📱 語感守護者：百科對照模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    st.text_area("試試只打「土豆」或完整句子：", height=150, 
                 value="洋芋片是土豆做的。", key="u_input")
    if st.button("🚀 執行語感偵測", use_container_width=True):
        st.session_state.current_text = st.session_state.u_input
        st.session_state.is_analyzed = True
    
    if st.session_state.is_analyzed:
        st.info("**最終文字預覽：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 語感專家建議")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            curr_text = st.session_state.current_text
            
            # A. 百科對照卡片 (最直覺的解釋)
            for word, info in WIKI_DICT.items():
                if word in curr_text:
                    with st.expander(f"📌 偵測到易混淆詞：{info['title']}", expanded=True):
                        st.write(f"🇹🇼 **台灣用法：** {info['tw_meaning']}")
                        st.write(f"🇨🇳 **中國用法：** {info['cn_meaning']}")
                        st.caption(f"💡 建議：{info['suggestion']}")
                        
                        # 提供轉換按鈕
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"換成「馬鈴薯」", key=f"btn_p_{word}", use_container_width=True):
                                apply_change(word, "馬鈴薯")
                                st.rerun()
                        with col_b:
                            if st.button(f"換成「花生」", key=f"btn_n_{word}", use_container_width=True):
                                apply_change(word, "花生")
                                st.rerun()

            # B. 一般詞彙修正
            for old, new in LOCAL_FIX.items():
                if old in curr_text:
                    st.button(f"📘 將「{old}」修正為「{new}」", key=f"fix_{old}", 
                              on_click=apply_change, args=(old, new), use_container_width=True)
        else:
            st.write("等待輸入中...")
