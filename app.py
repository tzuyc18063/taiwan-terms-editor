import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 配置與核心設定 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("❌ 找不到 API Key。請確保已在 Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'ai_results' not in st.session_state: st.session_state.ai_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# --- 2. 強化 AI 診斷邏輯 (增加嚴格指令) ---
def call_ai_expert(text):
    # 這裡大幅強化了對「口語詞」的偵測指令
    prompt = f"""
    你現在是一位極其嚴格的「台灣繁體中文語感檢察官」。
    你的任務是找出文字中任何屬於中國大陸的用語、口語、網路熱詞、或不符合台灣在地習慣的表達方式。
    
    【絕對必須偵測出的負面範例】：
    - 視頻 -> 影片
    - 質量 -> 品質
    - 很火/火了 -> 很紅/大受歡迎/熱門
    - 牛逼 -> 厲害/強/超強
    - 軟件 -> 軟體
    - 給力 -> 帶勁/夠意思
    - 接地氣 -> 親民/在地化
    
    請分析這段文字："{text}"
    
    請檢查是否有上述或其他大陸用語。如果文字中包含上述任何詞彙，絕對不能回傳「語感道地」。
    請務必只以 JSON 陣列格式回傳結果：
    [
      {{
        "original": "大陸詞彙",
        "taiwan": "台灣建議",
        "reason": "為什麼這在台灣不自然",
        "example": "台灣道地例句"
      }}
    ]
    若真的完全沒有大陸用語，才回傳空陣列 []。
    """
    try:
        response = model.generate_content(prompt)
        # 增加清洗邏輯，確保只拿 JSON
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except:
        return []

# --- 3. UI 介面 ---
st.title("📱 語感守護者：AI 深度偵測模式")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    u_input = st.text_area("請輸入內容：", height=200, 
                           value="這個視頻真的很火，質量非常牛逼。", key="u_input")
    
    if st.button("🚀 執行 AI 專家偵測", use_container_width=True):
        with st.spinner("檢察官正在嚴格掃描中..."):
            st.session_state.current_text = u_input
            st.session_state.ai_results = call_ai_expert(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.info("**最終文字預覽：**")
        st.markdown(f'<div style="background:#f0f2f6; padding:15px; border-radius:10px; border:1px solid #ddd;">{st.session_state.current_text}</div>', unsafe_allow_html=True)

with c2:
    st.subheader("🤳 語感專家診斷卡片")
    
    if st.session_state.is_analyzed:
        results = st.session_state.ai_results
        
        if not results:
            st.success("✨ 經過嚴格偵測，未發現明顯大陸用語！")
        else:
            st.warning(f"🚨 偵測到 {len(results)} 處非台灣道地用語：")
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
        st.write("請開始偵測...")

# 底部重置
if st.button("🧹 重置編輯器"):
    st.session_state.current_text = ""
    st.session_state.is_analyzed = False
    st.session_state.ai_results = []
    st.rerun()
