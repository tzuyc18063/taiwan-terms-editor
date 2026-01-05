import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

# --- 2. 核心初始化 (自動適應模型版本，防止 404) ---
def initialize_system():
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
            st.stop()
            
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # 動態抓取可用模型，確保不會因為名稱變動而 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        target = 'models/gemini-1.5-flash'
        if target not in available_models:
            # 如果找不到 flash，就自動選清單中第一個可用的
            target = available_models[0]
            
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"❌ 初始化失敗：{str(e)}")
        return None

model = initialize_system()

# --- 3. 狀態管理 ---
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    # 處理建議詞中可能有斜線的情況
    target_new = new.split(' / ')[0]
    st.session_state.current_text = st.session_state.current_text.replace(old, target_new)
    st.toast(f"✅ 已替換：{old} ➔ {target_new}")

# --- 4. 強化版語感分析邏輯 ---
def ai_data_analyze(text):
    if not text.strip():
        return []
        
    prompt = f"""
    你是一位精通兩岸語言差異的「台灣在地語感顧問」。
    請分析以下文字，找出不符合台灣在地習慣的詞彙（包含大陸用語、流行語、網路黑話如「蛐蛐」）。
    
    待分析文字："{text}"
    
    【回傳規範】：
    - 請嚴格以 JSON 陣列格式回傳。
    - 必須包含：original (原詞), taiwan (在地建議), reason (調整理由), example (在地範例)。
    - 若文字已完全符合台灣語感，請回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        # 使用正則表達式精準抓取 JSON 區塊，防止 AI 廢話導致白屏
        match = re.search(r'\[\s*{.*}\s*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        st.warning(f"⚠️ 掃描遇到一點問題，可能是網路波動，請再試一次。")
        return []

# --- 5. 介面呈現 ---
st.title("📱 語感守護者")
st.markdown("#### 運用 AI 大數據技術，協助您的文字更貼近台灣在地習慣")

c1, c2 = st.columns([1, 1.2])

with c1:
    with st.container():
        st.subheader("📝 輸入內容")
        # 這裡的 value 綁定 session_state，確保修正後內容會同步更新
        u_input = st.text_area("請輸入文字：", height=250, value=st.session_state.current_text if st.session_state.current_text else "這個套路真的很火，但他一直在背後蛐蛐我。", key="text_input")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 執行語感掃描", use_container_width=True):
                if u_input:
                    with st.spinner("語感顧問正在調閱大數據分析中..."):
                        st.session_state.current_text = u_input
                        st.session_state.final_results = ai_data_analyze(u_input)
                        st.session_state.is_analyzed = True
                        st.rerun()
        
        with col_btn2:
            if st.button("🧹 重置編輯器", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.is_analyzed = False
                st.session_state.final_results = []
                st.rerun()

    if st.session_state.is_analyzed:
        st.write("---")
        st.subheader("📋 修正後的文字")
        st.code(st.session_state.current_text, language=None)
        st.caption("💡 點擊右上方圖示即可快速複製。")

with c2:
    st.subheader("💡 語感調整建議")
    if st.session_state.is_analyzed:
        # 只顯示目前文字中還存在的錯誤
        active_results = [r for r in st.session_state.final_results if r['original'] in st.session_state.current_text]
        
        if not active_results:
            st.success("✨ 文字目前非常符合台灣在地的語感。")
        else:
            if st.button("🪄 一鍵套用所有建議", use_container_width=True):
                for item in active_results:
                    apply_change(item['original'], item['taiwan'])
                st.rerun()
                
            st.warning(f"🔔 發現 {len(active_results)} 處建議調整的詞彙：")
            for item in active_results:
                with st.expander(f"📌 在地建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                    st.write(f"📘 **理由：** {item['reason']}")
                    st.caption(f"📖 **在地範例：** {item['example']}")
                    if st.button(f"套用：{item['taiwan']}", key=f"btn_{item['original']}"):
                        apply_change(item['original'], item['taiwan'])
                        st.rerun()
    else:
        st.info("掃描後將在此顯示調整建議。")
