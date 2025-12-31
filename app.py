import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. 配置 ---
st.set_page_config(page_title="語感守護者 - AI 自動偵測版", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = "你的正確金鑰"

genai.configure(api_key=API_KEY)

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = {}
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

# --- 2. 核心 AI 邏輯 ---
def run_ai_analysis():
    text = st.session_state.u_input
    if not text: return
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 強化 Prompt：要求 AI 以 JSON 格式回傳，區分「直接替換」與「歧義選擇」
    prompt = f"""
    你是專業的台灣編輯。請分析以下文字中的中國用語，並區分為兩類回傳 JSON 格式：
    1. 'fix': 100% 確定要替換的詞（如：視頻->影片）。
    2. 'options': 語意分歧、在台灣有不同意思的詞（如：土豆、窩心）。
    
    JSON 格式範例：
    {{
      "fix": [ {{"old": "視頻", "new": "影片"}}, {{"old": "質量", "new": "品質"}} ],
      "options": [ {{"old": "土豆", "choices": ["馬鈴薯", "花生"], "desc": "中國指馬鈴薯，台灣指花生" }} ]
    }}
    
    文字內容：{text}
    """
    
    try:
        response = model.generate_content(prompt)
        # 清理 AI 可能回傳的 Markdown 語法
        clean_json = re.sub(r'```json|```', '', response.text).strip()
        st.session_state.analysis_results = json.loads(clean_json)
        st.session_state.current_text = text
        st.session_state.is_analyzed = True
    except Exception as e:
        st.error(f"AI 分析失敗，請檢查 API 額度或內容。錯誤：{e}")

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已更新：{new}")

# --- 3. UI 介面 ---
st.title("📱 語感守護者：AI 自動辨析歧義詞")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入區")
    st.text_area("試試輸入「我想吃土豆，順便看看視頻」：", height=150, key="u_input")
    st.button("🚀 AI 深度全自動偵測", on_click=run_ai_analysis, use_container_width=True)
    
    if st.session_state.is_analyzed:
        st.markdown("### 📝 修正後的最終文字")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 手機 App 互動模擬")
    
    with st.container(border=True):
        if st.session_state.is_analyzed:
            res = st.session_state.analysis_results
            
            with st.chat_message("assistant", avatar="🇹🇼"):
                st.write("🔍 **偵測報告 (AI 已自動掃描歧義)**")
                st.divider()
                
                # A. 顯示歧義選擇 (如：土豆)
                if 'options' in res and res['options']:
                    st.warning("⚠️ 發現歧義詞 (請依語境選擇)")
                    for item in res['options']:
                        old = item['old']
                        if old in st.session_state.current_text:
                            st.write(f"**「{old}」** 在兩岸意思不同：")
                            st.caption(item.get('desc', ''))
                            cols = st.columns(len(item['choices']))
                            for i, choice in enumerate(item['choices']):
                                with cols[i]:
                                    st.button(f"{choice}", key=f"opt_{old}_{i}", 
                                              on_click=apply_change, args=(old, choice), use_container_width=True)
                    st.divider()

                # B. 顯示直接替換
                if 'fix' in res and res['fix']:
                    st.caption("📘 中國用語建議修正")
                    for item in res['fix']:
                        old, new = item['old'], item['new']
                        if old in st.session_state.current_text:
                            st.button(f"將「{old}」換成「{new}」", key=f"fix_{old}", 
                                      on_click=apply_change, args=(old, new), use_container_width=True)
                
                if not res.get('fix') and not res.get('options'):
                    st.success("🎉 AI 沒發現任何中國用語，文字很道地！")
        else:
            st.info("👋 請輸入文字後點擊偵測。AI 會自動判斷哪些詞需要提供「多選一」。")

if st.session_state.is_analyzed:
    st.button("📋 一鍵複製成果", use_container_width=True)
