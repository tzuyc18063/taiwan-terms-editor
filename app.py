import streamlit as st
# 假設使用 Gemini API 作為背後運行機制
# import google.generativeai as genai 

# --- 1. 配置與核心資料 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 保留你原本手動建立的精華百科，作為 AI 無法連線時的保底
WIKI_DICT = {
    "土豆": {
        "title": "🥔 土豆 (Tǔ dòu)",
        "tw_meaning": "🥜 在台灣通常指「花生」",
        "cn_meaning": "🍟 在中國是指「馬鈴薯」",
        "suggestion": "建議根據語境換成「馬鈴薯」或「花生」。"
    }
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'ai_suggestions' not in st.session_state: st.session_state.ai_suggestions = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# 模擬 AI 在背後運行的邏輯 (未來可替換為真正的 API Call)
def ai_backend_analyze(text):
    # 這裡未來會接 AI：讓 AI 找出 text 裡面所有的大陸用語並給出台灣建議
    # 目前先以邏輯展示自動化偵測的結果
    detected = []
    if "質量" in text:
        detected.append({"word": "質量", "tw": "品質", "reason": "台灣習慣用品質，質量多指物理量。"})
    if "視頻" in text:
        detected.append({"word": "視頻", "tw": "影片", "reason": "台灣通用語為影片。"})
    return detected

# --- 2. UI 介面 ---
st.title("📱 語感守護者：AI 自動化模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    u_input = st.text_area("請輸入內容：", height=150, value="這個視頻的質量真的牛逼。", key="u_input")
    
    if st.button("🚀 執行 AI 語感掃描", use_container_width=True):
        st.session_state.current_text = u_input
        # AI 在背後運行：自動分析
        st.session_state.ai_suggestions = ai_backend_analyze(u_input)
        st.session_state.is_analyzed = True
    
    if st.session_state.is_analyzed:
        st.info("**最終文字預覽：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 AI 語感專家分析")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            # 1. 顯示手動百科 (你要求的基礎)
            for word, info in WIKI_DICT.items():
                if word in st.session_state.current_text:
                    with st.expander(f"📌 偵測到易混淆詞：{info['title']}", expanded=True):
                        st.write(f"🇹🇼 **台灣用法：** {info['tw_meaning']}")
                        st.caption(f"💡 建議：{info['suggestion']}")
                        if st.button(f"修正為馬鈴薯", key="fix_potato"): 
                            apply_change(word, "馬鈴薯")
                            st.rerun()

            # 2. 顯示 AI 自動偵測的結果 (不用手動新增庫)
            if st.session_state.ai_suggestions:
                st.divider()
                st.write("🤖 **AI 自動偵測到以下術語：**")
                for item in st.session_state.ai_suggestions:
                    if item['word'] in st.session_state.current_text:
                        with st.chat_message("assistant"):
                            st.write(f"建議將「**{item['word']}**」換成「**{item['tw']}**」")
                            st.caption(item['reason'])
                            if st.button(f"直接修正「{item['word']}」", key=f"ai_fix_{item['word']}"):
                                apply_change(item['word'], item['tw'])
                                st.rerun()
            else:
                st.write("未偵測到其他明顯的大陸用語。")
        else:
            st.write("請輸入文字並點擊掃描...")
