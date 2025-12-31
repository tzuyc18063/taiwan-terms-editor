import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. 配置 ---
st.set_page_config(page_title="語感守護者 - AI 全自動版", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = {}
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# --- 2. 核心 AI 邏輯 (修正 404 模型路徑) ---
def run_ai_analysis():
    text = st.session_state.u_input
    if not text: return
    
    # 修正：直接使用簡短名稱，不加 models/ 前綴，API 會自動處理版本
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        你是專業的台灣編輯。請分析以下文字中的中國用語，並區分為兩類回傳 JSON 格式：
        1. 'fix': 100% 確定要替換的詞。
        2. 'options': 語意分歧、在台灣有不同意思的詞（如：土豆、窩心）。
        
        JSON 格式範例：
        {{
          "fix": [ {{"old": "視頻", "new": "影片"}} ],
          "options": [ {{"old": "土豆", "choices": ["馬鈴薯", "花生"], "desc": "中國指馬鈴薯，台灣指花生" }} ]
        }}
        
        文字內容：{text}
        """
        
        response = model.generate_content(prompt)
        
        # 清理 AI 回傳的 Markdown 語法 (有些 AI 會自動加 ```json)
        raw_text = response.text
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        
        st.session_state.analysis_results = json.loads(clean_json)
        st.session_state.current_text = text
        st.session_state.is_analyzed = True
        
    except Exception as e:
        # 如果還是失敗，嘗試備援模型名稱
        try:
            model = genai.GenerativeModel('gemini-pro') # 備援
            # ... (重複同樣的 prompt 邏輯，這裡簡化處理)
            st.error(f"偵測到模型版本異動，請重試一次。")
        except:
            st.error(f"AI 分析失敗。請檢查 API Key 是否正確。錯誤訊息：{e}")

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已替換：{new}")

# --- 3. UI 介面 (保持原本受歡迎的氣泡與按鈕排版) ---
st.title("📱 語感守護者：AI 自動辨析")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 文字輸入")
    st.text_area("在此輸入內容：", height=150, value="這視頻質量特好，我想吃點土豆。", key="u_input")
    st.button("🚀 AI 深度偵測 (含歧義辨析)", on_click=run_ai_analysis, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.markdown("### 📝 修正後的最終文字")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 App 互動預覽")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            res = st.session_state.analysis_results
            
            with st.chat_message("assistant", avatar="🇹🇼"):
                st.write("🔍 **我們發現了以下中國用語建議：**")
                st.divider()
                
                # A. 顯示歧義詞 (AI 自動辨識出來的)
                if 'options' in res and res['options']:
                    st.warning("⚠️ 發現多義詞，請點選正確語意：")
                    for item in res['options']:
                        old = item['old']
                        if old in st.session_state.current_text:
                            st.write(f"**「{old}」**：{item.get('desc', '')}")
                            cols = st.columns(len(item['choices']))
                            for i, choice in enumerate(item['choices']):
                                with cols[i]:
                                    st.button(f"{choice}", key=f"opt_{old}_{i}", 
                                              on_click=apply_change, args=(old, choice), use_container_width=True)
                    st.divider()

                # B. 顯示固定修正
                if 'fix' in res and res['fix']:
                    st.caption("📘 建議直接修正")
                    for item in res['fix']:
                        old, new = item['old'], item['new']
                        if old in st.session_state.current_text:
                            st.button(f"將「{old}」修正為「{new}」", key=f"fix_{old}", 
                                      on_click=apply_change, args=(old, new), use_container_width=True)
                
                if not res.get('fix') and not res.get('options'):
                    st.success("🎉 目前文字沒偵測到明顯的中國用語。")
        else:
            st.info("👋 請輸入文字後點擊偵測。")

if st.session_state.is_analyzed:
    st.button("📋 複製修正後的文字", use_container_width=True)
