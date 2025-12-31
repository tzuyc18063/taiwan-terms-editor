import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 初始化設定 ---
st.set_page_config(page_title="語感專家", page_icon="📱", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 核心 AI 邏輯：強制 AI 進行全句語感分析 ---
def start_deep_analysis(text):
    if not text.strip(): return []
    
    # 使用 1.5-flash 確保速度與辨識度
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 這裡的 Prompt 強化了對「內卷」、「躺平」等新詞的自動抓取
    prompt = f"""
    任務：你是最嚴格的台灣語境校正員。請找出這段文字中「任何」不符合台灣在地習慣的詞彙（包含流行語、語法、職場用語）。
    待分析文字："{text}"
    
    【辨識重點】：
    - 職場新詞：內卷 (建議:過度競爭)、躺平、畫餅、賦能。
    - 語法不自然：有被驚訝到、給到。
    - 網路流行：媽生好皮、種草、氛圍感、特好。
    
    請直接生成百科內容，並僅回傳 JSON 格式列表：
    [
      {{
        "original": "抓到的原詞",
        "replacement": "台灣在地建議說法",
        "title": "百科標題 (例如: 內卷 vs 過度競爭)",
        "explanation": "說明這個詞在大陸的意思，以及為什麼在台灣不常用。",
        "suggestion": "具體的修正操作建議"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt)
        # 提取 JSON 區塊，避免 AI 回傳額外文字導致出錯
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return []
    except Exception as e:
        # 若 AI 出錯（如截圖 3 的 404），回傳自定義錯誤提示
        st.error(f"⚠️ AI 服務目前無法連線，請檢查 API Key 或稍後再試。")
        return []

# --- 3. 介面與狀態管理 ---
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'results' not in st.session_state: st.session_state.results = []
if 'analyzed' not in st.session_state: st.session_state.analyzed = False

def apply_fix(old, new):
    st.session_state.processed_text = st.session_state.processed_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# --- 4. UI 介面 ---
st.title("📱 語感專家：終極全自動辨識")
st.caption("結合 AI 即時分析，自動抓取如「內卷」、「媽生」等所有非在地詞彙。")

col_in, col_wiki = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("請輸入您想檢查的內容：", height=250, value="現在職場太內卷，大家都想躺平，這視頻真的很火。")
    
    if st.button("🚀 啟動深度智慧掃描", use_container_width=True):
        st.session_state.processed_text = u_input
        with st.spinner("AI 正全力辨識所有不道地用語..."):
            st.session_state.results = start_deep_analysis(u_input)
            st.session_state.analyzed = True

    if st.session_state.analyzed:
        st.markdown("### 📋 修正後結果預覽")
        st.code(st.session_state.processed_text, language=None)

with col_right := col_wiki:
    st.subheader("🤳 台灣語境百科對照")
    if st.session_state.analyzed:
        # 過濾目前文字中還存在的詞
        active_items = [r for r in st.session_state.results if r['original'] in st.session_state.processed_text]
        
        if not active_items:
            st.success("🎉 完美！這段文字目前讀起來非常道地。")
        else:
            for item in active_items:
                with st.expander(f"✨ 自動偵測：{item['original']}", expanded=True):
                    st.markdown(f"### {item['title']}")
                    st.write(f"🔍 **語境百科：** {item['explanation']}")
                    st.info(f"💡 **建議：** {item['suggestion']}")
                    
                    if st.button(f"👉 修正為「{item['replacement']}」", key=f"fix_{item['original']}", use_container_width=True):
                        apply_fix(item['original'], item['replacement'])
                        st.rerun()
    else:
        st.info("👋 請在左側輸入文字後啟動掃描。")
