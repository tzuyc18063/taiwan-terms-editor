import streamlit as st

# --- 1. 配置與語境百科資料 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# 這裡建立完整的語境資料庫
KNOWLEDGE_BASE = {
    "視頻": {
        "title": "📺 視頻 vs 影片",
        "tw_term": "影片",
        "explanation": "在台灣，日常生活中稱呼動態影像為「影片」。\n「視頻」在台灣多指電子工程中的「視訊訊號」。",
        "example": "「這段視頻很有趣」 👉 台灣建議用「這段影片很有趣」"
    },
    "土豆": {
        "title": "🥔 土豆的語意陷阱",
        "tw_term": "馬鈴薯 / 花生",
        "explanation": "中國的土豆指「馬鈴薯」(Potato)。\n台灣的土豆指「花生」(Peanut)。",
        "example": "「洋芋片是土豆做的」 👉 台灣應換成「馬鈴薯」。"
    },
    "質量": {
        "title": "⚖️ 質量 vs 品質",
        "tw_term": "品質",
        "explanation": "中國指產品優劣。在台灣，「質量」指物理學重量(Mass)，「品質」才指優劣(Quality)。",
        "example": "「這衣服質量真好」 👉 台灣建議用「這衣服品質真好」"
    }
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已為您修正語境：{new}")

# --- 2. UI 介面 ---
st.title("📱 語感守護者：語境百科模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("試試貼上：這視頻質量特好，洋芋片是土豆做的。", height=150, key="u_input")
    if st.button("🚀 深度語感偵測", use_container_width=True):
        st.session_state.current_text = u_input
        st.session_state.is_analyzed = True
    
    if st.session_state.is_analyzed:
        st.success("**修正後文字預覽：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 台灣語境專家建議")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            curr_text = st.session_state.current_text
            found = False
            
            # 遍歷資料庫進行「百科式」呈現
            for word, info in KNOWLEDGE_BASE.items():
                if word in curr_text:
                    found = True
                    # 使用 Styled Card 模擬手機 App 彈窗
                    with st.expander(f"💡 發現中國用語：{word}", expanded=True):
                        st.markdown(f"#### {info['title']}")
                        st.write(info['explanation'])
                        st.caption(f"📝 範例：{info['example']}")
                        
                        # 根據該詞提供不同的轉換按鈕
                        if word == "土豆":
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("🥜 換成 花生", key="btn_peanut", use_container_width=True):
                                    apply_change(word, "花生")
                                    st.rerun()
                            with col_b:
                                if st.button("🍟 換成 馬鈴薯", key="btn_potato", use_container_width=True):
                                    apply_change(word, "馬鈴薯")
                                    st.rerun()
                        else:
                            if st.button(f"👉 修正為台灣語境：{info['tw_term']}", key=f"btn_{word}", use_container_width=True):
                                apply_change(word, info['tw_term'])
                                st.rerun()
            
            if not found:
                st.success("🎉 這段文字很有台灣味，沒有偵測到需要解釋的詞彙。")
        else:
            st.info("👋 請輸入文字後點擊偵測。")
