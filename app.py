import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. 配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = {}
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# --- 2. 自動尋找可用模型函數 ---
def get_model():
    # 自動尋找目前環境支援的模型名稱
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name:
                    return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-pro') # 備援
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

# --- 3. 強化 AI 解析邏輯 ---
def run_ai_analysis():
    text = st.session_state.u_input
    if not text: return
    
    # 這裡呼叫自動尋找的模型
    model = get_model()
    
    prompt = f"""
    你是專業的台灣編輯。請分析以下文字中的中國用語，並區分為兩類回傳 JSON 格式：
    1. 'fix': 100% 確定要替換的詞。
    2. 'options': 語意分歧、在台灣有不同意思的詞（如：土豆、窩心）。
    
    注意：僅輸出 JSON 內容，不要包含任何解釋文字。
    JSON 格式範例：
    {{
      "fix": [ {{"old": "視頻", "new": "影片"}} ],
      "options": [ {{"old": "土豆", "choices": ["馬鈴薯", "花生"], "desc": "中國指馬鈴薯，台灣指花生" }} ]
    }}
    
    文字內容：{text}
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text
        
        # 抓取 JSON 區塊
        json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if json_match:
            st.session_state.analysis_results = json.loads(json_match.group(0))
            st.session_state.current_text = text
            st.session_state.is_analyzed = True
        else:
            st.error("AI 格式解析錯誤，請再點擊一次偵測。")
            
    except Exception as e:
        st.error(f"連線失敗，請檢查 API Key。錯誤詳細內容：{str(e)}")

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已更新：{new}")

# --- 4. UI 介面 ---
st.title("📱 語感守護者：AI 全自動辨析")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    st.text_area("在此輸入內容：", height=150, value="這視頻質量特好，我想吃點土豆。", key="u_input")
    st.button("🚀 執行深度偵測", on_click=run_ai_analysis, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.markdown("### 📝 修正後的最終文字")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 App 互動預覽")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            res = st.session_state.analysis_results
            with st.chat_message("assistant", avatar="🇹🇼"):
                st.write("🔍 **偵測報告：**")
                
                # 歧義詞處理
                if 'options' in res and res['options']:
                    st.warning("⚠️ 發現多義詞：")
                    for item in res['options']:
                        old = item['old']
                        if old in st.session_state.current_text:
                            st.write(f"**「{old}」**：{item.get('desc', '')}")
                            cols = st.columns(len(item['choices']))
                            for i, choice in enumerate(item['choices']):
                                with cols[i]:
                                    st.button(f"{choice}", key=f"opt_{old}_{i}", on_click=apply_change, args=(old, choice), use_container_width=True)
                
                # 固定修正處理
                if 'fix' in res and res['fix']:
                    st.caption("📘 中國用語建議修正")
                    for item in res['fix']:
                        old, new = item['old'], item['new']
                        if old in st.session_state.current_text:
                            st.button(f"將「{old}」換成「{new}」", key=f"fix_{old}", on_click=apply_change, args=(old, new), use_container_width=True)
        else:
            st.info("👋 請輸入文字後點擊偵測。")

if st.session_state.is_analyzed:
    st.button("📋 複製最終成果", use_container_width=True)
