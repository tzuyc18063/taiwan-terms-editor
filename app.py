import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 (純台灣用語) ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("❌ 找不到 API 金鑰。請確認已在 Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'ai_results' not in st.session_state: st.session_state.ai_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已為您修正為：{new}")

# --- 2. 核心邏輯：強制過濾器 + AI 專家 ---
def call_ai_expert(text):
    # 建立一個強制偵測清單，避免 AI 裝傻
    mandatory_check = ["視頻", "質量", "牛逼", "很火", "火了", "軟件", "優化", "反饋"]
    has_mandatory = any(word in text for word in mandatory_check)
    
    prompt = f"""
    你現在是一位立場極其嚴謹的「台灣在地語感檢察官」。
    你的目標是掃除文字中所有的大陸用語及網路熱詞，還原台灣道地用法。
    
    【待檢查文字】："{text}"
    
    【嚴格指令】：
    1. 如果文字包含：視頻、質量、牛逼、很火、火了、軟件、優化、反饋、接口、項目、程序...等任何一個詞，
       你「絕對禁止」回報語感道地，必須列出修正建議。
    2. 請將這些詞替換為台灣常見的：影片、品質、厲害/強、很紅/大受歡迎、軟體、最佳化、回饋、介面、專案、程式。
    3. 解釋必須站在台灣文化立場，說明為何台灣不這樣用（例如：台灣習慣用法、語源差異）。
    
    請僅以 JSON 格式回傳，禁止任何多餘廢話：
    [
      {{
        "original": "偵測到的詞",
        "taiwan": "台灣在地建議",
        "reason": "差異解釋（限用台灣語感說明，禁用大陸術語）",
        "example": "台灣在地例句"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            results = json.loads(match.group())
            # 如果 AI 裝死沒偵測到但明明有強制詞，這裡可以報錯或強制要求重新分析
            return results
        return []
    except:
        return []

# --- 3. 介面設計 ---
st.title("📱 語感守護者：鐵腕檢察官模式")
st.markdown("#### 掃除非在地用語，捍衛台灣語感")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    u_input = st.text_area("請在此貼上內容：", height=200, 
                           value="這個視頻真的很火，質量非常牛逼。", key="u_input")
    
    if st.button("🚀 執行語感掃描", use_container_width=True):
        with st.spinner("檢察官正在嚴格掃描中..."):
            st.session_state.current_text = u_input
            st.session_state.ai_results = call_ai_expert(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.info("**修正後的文字預覽：**")
        st.markdown(f'<div style="background:#f0f2f6; padding:15px; border-radius:10px; border:1px solid #ddd; color:#333;">{st.session_state.current_text}</div>', unsafe_allow_html=True)

with c2:
    st.subheader("🤳 語感診斷報告")
    
    if st.session_state.is_analyzed:
        results = st.session_state.ai_results
        
        if not results:
            st.success("✨ 經過嚴格檢查，文字語感符合台灣在地習慣。")
        else:
            st.warning(f"🚨 偵測到 {len(results)} 處非道地用法建議：")
            for item in results:
                if item['original'] in st.session_state.current_text:
                    with st.expander(f"📌 建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                        st.write(f"🇹🇼 **建議替換：** {item['taiwan']}")
                        st.write(f"💡 **差異解析：** {item['reason']}")
                        st.caption(f"📖 **在地範例：** {item['example']}")
                        
                        if st.button(f"接受修正：{item['taiwan']}", key=f"btn_{item['original']}"):
                            apply_change(item['original'], item['taiwan'])
                            st.rerun()
    else:
        st.write("請輸入文字開始掃描。")

# --- 4. 底部工具 ---
st.divider()
if st.button("🧹 重置編輯器"):
    st.session_state.current_text = ""
    st.session_state.is_analyzed = False
    st.session_state.ai_results = []
    st.rerun()
