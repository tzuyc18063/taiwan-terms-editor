import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與初始化 ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 核心 AI 引擎：全自動語感過濾 ---
def auto_detect_and_wiki(text):
    """叫 AI 找出所有大陸用語，並同步生成百科內容"""
    if not text.strip(): return []
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    任務：你是兩岸用語百科專家。請分析以下文字中不符合「台灣道地口語」的大陸用語或熱詞。
    
    待分析文字："{text}"
    
    要求：
    1. 找出所有大陸用語（如：媽生好皮、很火、視頻、質量、優化、水平、立馬等）。
    2. 針對每個詞，生成一張百科卡片資料。
    3. 台灣人形容皮膚不會用「好皮」，必須改為「好皮膚」或「膚質好」。
    
    請僅回傳 JSON 格式列表，格式如下：
    [
      {{
        "original": "原詞",
        "replacement": "台灣道地建議",
        "title": "百科標題 (如: 媽生好皮 vs 天生好皮膚)",
        "explanation": "為什麼這在大陸流行？台灣習慣怎麼說？",
        "suggestion": "給使用者的修正建議"
      }}
    ]
    若無偵測到任何詞，請回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        # 提取 JSON 區塊
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return []
    except Exception as e:
        st.error(f"AI 偵測出錯：{e}")
        return []

# --- 3. 狀態與介面邏輯 ---
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'wiki_cards' not in st.session_state: st.session_state.wiki_cards = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_correction(old, new):
    st.session_state.processed_text = st.session_state.processed_text.replace(old, new)
    # 修正後重新檢查卡片，若詞已不存在則隱藏
    st.toast(f"✅ 已修正為：{new}")

# --- 4. UI 呈現 ---
st.title("📱 語感專家：AI 全自動百科偵測")
st.caption("輸入任何文字，AI 將自動識別大陸用語並為您即時編寫對照百科。")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入任何文字（如：這視頻很火，能打造媽生好皮）：", height=250)
    
    if st.button("🚀 執行全自動語感掃描", use_container_width=True):
        with st.spinner("AI 正在深度掃描並編寫百科中..."):
            results = auto_detect_and_wiki(u_input)
            st.session_state.processed_text = u_input
            st.session_state.wiki_cards = results
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("---")
        st.markdown("### 📋 修正後結果預覽")
        st.code(st.session_state.processed_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.is_analyzed:
        active_cards = [card for card in st.session_state.wiki_cards if card['original'] in st.session_state.processed_text]
        
        if not active_cards:
            st.success("🎉 完美！這段文字目前非常符合台灣在地語感。")
        else:
            for item in active_cards:
                with st.expander(f"📌 百科發現：{item['original']}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(f"🔍 **語境百科：** {item['explanation']}")
                    st.info(f"💡 **建議：** {item['suggestion']}")
                    
                    btn_label = f"👉 修正為「{item['replacement']}」"
                    if st.button(btn_label, key=f"btn_{item['original']}", use_container_width=True):
                        apply_correction(item['original'], item['replacement'])
                        st.rerun()
    else:
        st.info("👋 在左側輸入任何內容並點擊掃描，我會自動幫您找出所有不地道的用法。")
