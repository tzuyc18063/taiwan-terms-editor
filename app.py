import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("❌ 找不到 API 金鑰。請確認已在 Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

# --- 2. 鐵腕硬核過濾名單 (不經 AI，直接強制抓取) ---
HARDCORE_RULES = {
    "視頻": {"tw": "影片", "reason": "台灣道地用語為「影片」，「視頻」為大陸用語。", "example": "這部影片拍得真好。"},
    "質量": {"tw": "品質", "reason": "形容東西好壞請用「品質」，「質量」在台灣多指物理重量。", "example": "這間餐廳的服務品質很高。"},
    "很火": {"tw": "很紅 / 熱門", "reason": "台灣習慣用「很紅」或「大受歡迎」，「很火」是大陸流行語。", "example": "這首歌最近在台灣很紅。"},
    "牛逼": {"tw": "厲害 / 強", "reason": "「牛逼」是大陸北方粗俗口語，台灣建議用「厲害」或「超強」。", "example": "你的程式技術真的太厲害了。"},
    "軟件": {"tw": "軟體", "reason": "台灣將 Software 譯為「軟體」，與「硬體」成對。", "example": "這套軟體非常實用。"},
    "反饋": {"tw": "回饋", "reason": "台灣習慣用「回饋」或「響應」，「反饋」多為大陸用語。", "example": "感謝您提供的回饋意見。"}
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# --- 3. 混合分析邏輯 ---
def heavy_analyze(text):
    results = []
    
    # 第一層：強制過濾 (鐵腕硬過濾，AI 攔不住)
    for cn, info in HARDCORE_RULES.items():
        if cn in text:
            results.append({
                "original": cn,
                "taiwan": info["tw"],
                "reason": f"【強制偵測】{info['reason']}",
                "example": info["example"]
            })
    
    # 第二層：AI 深度偵測 (捕捉其他漏網之魚)
    prompt = f"""
    你是一位極其嚴格的台灣語感專家。分析文字中不符合台灣語感的詞彙。
    除了已被偵測出的詞彙，請找出其他大陸用語。
    待分析文字："{text}"
    請務必回傳 JSON 陣列格式。若無則回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
            # 排除掉已經在強制名單裡的重複項
            for item in ai_data:
                if not any(r['original'] == item['original'] for r in results):
                    results.append(item)
    except:
        pass
        
    return results

# --- 4. 使用者介面 ---
st.title("📱 語感守護者：真正鐵腕模式")
st.markdown("#### 強制過濾 + AI 雙重把關，絕不姑息大陸用語")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    u_input = st.text_area("請在此貼上內容：", height=200, 
                           value="這個視頻真的很火，質量非常牛逼。", key="u_input")
    
    if st.button("🚀 執行鐵腕掃描", use_container_width=True):
        with st.spinner("檢察官正在執法中..."):
            st.session_state.current_text = u_input
            st.session_state.final_results = heavy_analyze(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.info("**預覽內容：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 鐵腕診斷卡片")
    
    if st.session_state.is_analyzed:
        res = st.session_state.final_results
        
        if not res:
            st.success("✨ 經過鐵腕檢查，文字完全符合台灣在地習慣。")
        else:
            st.error(f"🚨 抓到 {len(res)} 處違規用語！")
            for item in res:
                if item['original'] in st.session_state.current_text:
                    with st.expander(f"📌 強制修正：{item['original']} ➔ {item['taiwan']}", expanded=True):
                        st.write(f"🇹🇼 **建議替換：** {item['taiwan']}")
                        st.write(f"💡 **差異解析：** {item['reason']}")
                        st.caption(f"📖 **在地範例：** {item['example']}")
                        
                        if st.button(f"立即執行修正：{item['taiwan']}", key=f"btn_{item['original']}"):
                            apply_change(item['original'], item['taiwan'])
                            st.rerun()
    else:
        st.write("請輸入文字開始掃描。")

# 底部重置
if st.button("🧹 重置編輯器"):
    st.session_state.current_text = ""
    st.session_state.is_analyzed = False
    st.session_state.final_results = []
    st.rerun()
