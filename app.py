import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 (使用溫和專業的用語) ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("❌ 系統提示：請確認 API 金鑰設定是否正確。")
    st.stop()

# --- 2. 在地語感資料庫 (口吻調整為緩和說明) ---
HARDCORE_RULES = {
    "套路": {"tw": "花招 / 陷阱 / 慣用手段", "reason": "「套路」在大陸多指精心策劃的應對方式；台灣道地說法通常使用「花招」、「話術」或「手段」會更自然。", "example": "這都是商家的行銷花招。"},
    "走心": {"tw": "用心 / 認真 / 觸動內心", "reason": "大陸語境中「走心」指用心；但在台灣傳統語意中，「走心」有時帶有「在意、鑽牛角尖」的負面意涵，建議依語境調整。", "example": "這部電影的劇情非常動人。"},
    "視頻": {"tw": "影片", "reason": "台灣在地習慣稱為「影片」，建議調整以符合台灣讀者的閱讀習慣。", "example": "這部影片剪輯得很專業。"},
    "很火": {"tw": "很紅 / 大受歡迎", "reason": "台灣習慣用「很紅」或「熱門」來形容受歡迎的程度。", "example": "這款手遊最近在台灣非常紅。"},
    "牛逼": {"tw": "厲害 / 強", "reason": "「牛逼」在台灣語感中較為生硬，建議使用「厲害」或「超強」會更親切。", "example": "你的技術真的太厲害了。"},
    "質量": {"tw": "品質", "reason": "在形容物品的優劣時，台灣習慣使用「品質」一詞。", "example": "這台筆電的硬體品質很好。"},
    "優化": {"tw": "最佳化 / 改善", "reason": "在科技領域台灣多稱「最佳化」，生活用語則建議使用「改善」或「調整」。", "example": "系統效能需要進一步最佳化。"},
    "反饋": {"tw": "回饋 / 響應", "reason": "台灣習慣使用「回饋」來指代意見反應。", "example": "感謝您提供的回饋意見。"}
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已為您更新為：{new}")

# --- 3. 語感分析邏輯 ---
def heavy_analyze(text):
    results = []
    # 第一層：精確比對
    for cn, info in HARDCORE_RULES.items():
        if cn in text:
            results.append({
                "original": cn,
                "taiwan": info["tw"],
                "reason": info["reason"],
                "example": info["example"]
            })
    
    # 第二層：AI 輔助掃描 (設定專家語氣為緩和)
    prompt = f"""
    你是一位台灣語感顧問。請分析以下文字中，哪些詞彙在台灣較不常見，並提供更道地的在地建議。
    請用緩和、有禮貌的口吻進行解釋。
    待分析文字："{text}"
    請回傳 JSON 陣列，若文字已經很道地，請回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
            for item in ai_data:
                if not any(r['original'] == item['original'] for r in results):
                    results.append(item)
    except:
        pass
    return results

# --- 4. 介面呈現 ---
st.title("📱 語感守護者")
st.markdown("#### 協助您優化文字，更貼近台灣在地的表達習慣")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入內容")
    u_input = st.text_area("請在此輸入或貼上文字：", height=200, 
                           value="這個套路真的很火，視頻質量牛逼。", key="u_input")
    
    if st.button("🚀 進行語感掃描", use_container_width=True):
        with st.spinner("語感顧問正在分析中..."):
            st.session_state.current_text = u_input
            st.session_state.final_results = heavy_analyze(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.info("**文字更新預覽：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("💡 語感調整建議")
    
    if st.session_state.is_analyzed:
        res = st.session_state.final_results
        
        if not res:
            st.success("✨ 經過檢查，這段文字非常符合台灣在地的語感。")
        else:
            # 修改為緩和的提示語
            st.warning(f"🔔 偵測到 {len(res)} 處建議調整的詞彙：")
            for item in res:
                if item['original'] in st.session_state.current_text:
                    with st.expander(f"📌 在地建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                        st.write(f"🇹🇼 **台灣慣用：** {item['taiwan']}")
                        st.write(f"📘 **調整建議：** {item['reason']}")
                        st.caption(f"📖 **在地範例：** {item['example']}")
                        
                        if st.button(f"套用建議：{item['taiwan']}", key=f"btn_{item['original']}"):
                            apply_change(item['original'], item['taiwan'])
                            st.rerun()
    else:
        st.write("等待掃描結果...")

# 底部重置
if st.button("🧹 重置編輯器"):
    st.session_state.current_text = ""
    st.session_state.is_analyzed = False
    st.session_state.final_results = []
    st.rerun()
