import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 核心初始化 ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

# 修正 API 初始化方式
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("請在 Secrets 中設定 GOOGLE_API_KEY")

# 建立一個基礎詞庫作為保險，確保 100% 觸發
BASE_WIKI = {
    "媽生好皮": {"to": "天生好皮膚", "title": "✨ 媽生好皮 vs 天生好皮膚", "desc": "台灣不說「好皮」，請完整修正為「好皮膚」。"},
    "視頻": {"to": "影片", "title": "📺 視頻 vs 影片", "desc": "台灣日常習慣稱呼為「影片」。"},
    "很火": {"to": "很紅", "title": "🔥 很火 vs 很紅/熱門", "desc": "台灣習慣用「很紅」、「很夯」或「熱門」。"}
}

# --- 2. 核心 AI 引擎 (修正 404 錯誤) ---
def auto_detect_and_wiki(text):
    if not text.strip(): return []
    
    # 確保使用正確的模型名稱
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    你現在是台灣語境專家。請分析以下文字中不符合「台灣道地口語」的大陸用語或熱詞。
    輸入文字："{text}"
    
    要求：
    1. 找出所有大陸用語（包含：媽生好皮、很火、優化、水平、視頻等）。
    2. 針對每個詞，生成百科內容。
    3. 台灣人形容皮膚不說「好皮」，必須改為「好皮膚」。
    
    請僅回傳 JSON 列表：
    [
      {{
        "original": "原詞",
        "replacement": "台灣道地建議",
        "title": "百科標題",
        "explanation": "差異解釋",
        "suggestion": "修正建議"
      }}
    ]
    """
    try:
        # 移除 version 參數，讓 SDK 自動處理
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except Exception as e:
        # 如果 AI 失敗，回傳空清單，由後方的本地邏輯補位
        return []

# --- 3. 介面邏輯 ---
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'wiki_cards' not in st.session_state: st.session_state.wiki_cards = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_correction(old, new):
    st.session_state.processed_text = st.session_state.processed_text.replace(old, new)
    st.toast(f"✅ 已修正：{new}")

# --- 4. UI 呈現 ---
st.title("📱 語感專家：AI 全自動百科偵測")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入任何文字：", height=250, value="這視頻很火，能教你打造媽生好皮")
    
    if st.button("🚀 執行全自動語感掃描", use_container_width=True):
        st.session_state.processed_text = u_input
        with st.spinner("掃描中..."):
            # 1. AI 偵測
            ai_results = auto_detect_and_wiki(u_input)
            
            # 2. 本地補位邏輯 (確保 AI 斷線時，基本詞還能動)
            final_cards = ai_results
            ai_detected_words = [r['original'] for r in ai_results]
            
            for word, info in BASE_WIKI.items():
                if word in u_input and word not in ai_detected_words:
                    final_cards.append({
                        "original": word,
                        "replacement": info['to'],
                        "title": info['title'],
                        "explanation": info['desc'],
                        "suggestion": f"建議換成「{info['to']}」"
                    })
            
            st.session_state.wiki_cards = final_cards
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.markdown("### 📋 修正後結果")
        st.code(st.session_state.processed_text, language=None)

with c2:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.is_analyzed:
        # 只顯示目前文字中還存在的詞
        active_cards = [c for c in st.session_state.wiki_cards if c['original'] in st.session_state.processed_text]
        
        if not active_cards:
            st.success("🎉 目前文字看起來非常本土！")
        else:
            for item in active_cards:
                with st.expander(f"📌 百科發現：{item['original']}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(item['explanation'])
                    if st.button(f"👉 修正為「{item['replacement']}」", key=f"btn_{item['original']}", use_container_width=True):
                        apply_correction(item['original'], item['replacement'])
                        st.rerun()
