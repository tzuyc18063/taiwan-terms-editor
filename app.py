import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. 配置與模型鎖定 ---
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

# 強制尋找可用模型（徹底解決 404 問題）
@st.cache_resource
def init_model():
    try:
        # 取得目前 API 金鑰下所有可用的模型清單
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順序：1.5 Flash > 1.0 Pro
        target_models = ['models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.0-pro']
        
        for target in target_models:
            if target in available_models:
                return genai.GenerativeModel(model_name=target)
        
        # 如果都沒有，就用清單中第一個可用的
        return genai.GenerativeModel(model_name=available_models[0])
    except Exception as e:
        # 最後的保險手段
        return genai.GenerativeModel(model_name='gemini-1.5-flash')

# --- 2. 強化 AI 解析邏輯 ---
def run_ai_analysis():
    text = st.session_state.u_input
    if not text: return
    
    model = init_model()
    
    prompt = f"""
    你是專業的台灣編輯。請分析以下文字中的中國用語，並區分為兩類回傳 JSON 格式：
    1. 'fix': 確定要替換的詞（如：視頻->影片）。
    2. 'options': 語意分歧、在台灣有不同意思的詞（如：土豆、窩心）。
    
    注意：僅輸出 JSON 內容，不要有 markdown 標籤。
    格式：
    {{
      "fix": [ {{"old": "中國用語", "new": "台灣用語"}} ],
      "options": [ {{"old": "歧義詞", "choices": ["選項1", "選項2"], "desc": "解釋" }} ]
    }}
    
    文字：{text}
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text
        
        # 精準過濾 JSON 內容
        json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if json_match:
            st.session_state.analysis_results = json.loads(json_match.group(0))
            st.session_state.current_text = text
            st.session_state.is_analyzed = True
        else:
            st.error("AI 回傳格式有誤，請再試一次。")
            
    except Exception as e:
        st.error(f"目前與 Google AI 連線失敗。錯誤代碼：{str(e)}")

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已替換：{new}")

# --- 3. UI 介面 ---
st.title("📱 語感守護者：中國用語全自動辨析")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    st.text_area("試試貼上包含「土豆」或「視頻」的文字：", height=150, value="這視頻質量特好，我想吃點土豆。", key="u_input")
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
                st.write("🔍 **中國用語偵測報告：**")
                
                # A. 處理歧義詞 (二選一)
                if 'options' in res and res['options']:
                    st.warning("⚠️ 發現多義詞：")
                    for item in res['options']:
                        old = item['old']
                        if old in st.session_state.current_text:
                            st.write(f"**「{old}」**：{item.get('desc', '')}")
                            choices = item['choices']
                            cols = st.columns(len(choices))
                            for i, choice in enumerate(choices):
                                with cols[i]:
                                    st.button(f"{choice}", key=f"opt_{old}_{i}", on_click=apply_change, args=(old, choice), use_container_width=True)
                
                # B. 處理直接修正
                if 'fix' in res and res['fix']:
                    st.caption("📘 建議直接修正")
                    for item in res['fix']:
                        old, new = item['old'], item['new']
                        if old in st.session_state.current_text:
                            st.button(f"將「{old}」換成「{new}」", key=f"fix_{old}", on_click=apply_change, args=(old, new), use_container_width=True)
                
                if not res.get('fix') and not res.get('options'):
                    st.success("🎉 文字檢查通過！")
        else:
            st.info("👋 請輸入文字後點擊偵測。")

if st.session_state.is_analyzed:
    st.button("📋 複製成果", use_container_width=True)
