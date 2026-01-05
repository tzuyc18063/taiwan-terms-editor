import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. 頁面配置 ---
st.set_page_config(page_title="語感守護者", page_icon="📱", layout="wide")

try:
    # 讀取 Secrets 中的金鑰
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("❌ 系統提示：請確認 API 金鑰設定（GEMINI_API_KEY）是否正確。")
    st.stop()

# --- 2. 在地語感資料庫 (緩和口吻說明) ---
HARDCORE_RULES = {
    "套路": {"tw": "花招 / 陷阱 / 慣用手段", "reason": "「套路」在台灣道地說法中，通常使用「花招」、「話術」或「手段」會更自然。"},
    "走心": {"tw": "用心 / 認真", "reason": "「走心」在台灣傳統語意中有時帶有「在意、鑽牛角尖」的含意，建議依語境調整。"},
    "視頻": {"tw": "影片", "reason": "台灣在地習慣稱為「影片」，調整後更符合台灣讀者的閱讀習慣。"},
    "很火": {"tw": "很紅 / 大受歡迎", "reason": "台灣習慣用「很紅」或「熱門」來形容受歡迎的程度。"},
    "牛逼": {"tw": "厲害 / 強", "reason": "建議使用「厲害」或「超強」會更親切且道地。"},
    "質量": {"tw": "品質", "reason": "形容物品優劣時，台灣習慣使用「品質」一詞。"},
    "優化": {"tw": "最佳化 / 改善", "reason": "科技領域台灣多稱「最佳化」，生活語法建議使用「改善」。"},
    "反饋": {"tw": "回饋 / 響應", "reason": "台灣習慣使用「回饋」來指代意見反應。"}
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已套用建議：{new}")

def heavy_analyze(text):
    results = []
    # 第一層：精確比對
    for cn, info in HARDCORE_RULES.items():
        if cn in text:
            results.append({"original": cn, "taiwan": info["tw"], "reason": info["reason"]})
    
    # 第二層：AI 輔助掃描
    prompt = f"你是一位台灣語感顧問。請找出文字中在台灣較不常見的詞彙並提供建議（如：大陸用語或流行語）。文字：{text}。請僅回傳 JSON 陣列格式。"
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
            for item in ai_data:
                if not any(r['original'] == item['original'] for r in results):
                    results.append(item)
    except: pass
    return results

# --- 3. 使用者介面 ---
st.title("📱 語感守護者")
st.markdown("#### 協助您的文字更貼近台灣在地的表達習慣")

c1, c2 = st.columns([1, 1.2])

with c1:
    # 固定左側容器，避免按鈕位移
    with st.container():
        st.subheader("📝 輸入內容")
        u_input = st.text_area("請在此輸入文字：", height=250, 
                               value="這個套路真的很火，視頻質量牛逼。", key="u_input")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 執行語感掃描", use_container_width=True):
                with st.spinner("語感顧問分析中..."):
                    st.session_state.current_text = u_input
                    st.session_state.final_results = heavy_analyze(u_input)
                    st.session_state.is_analyzed = True
        
        with col_btn2:
            if st.button("🧹 重置編輯器", use_container_width=True):
                st.session_state.current_text = ""
                st.session_state.is_analyzed = False
                st.session_state.final_results = []
                st.rerun()

    # 文字預覽與一鍵複製區
    if st.session_state.is_analyzed:
        st.write("---")
        st.subheader("📋 修正後的文字")
        # 使用 st.code 內建的複製按鈕，這是最穩定的複製方案
        st.code(st.session_state.current_text, language=None)
        st.caption("💡 點擊右上方圖示即可快速複製文字。")

with c2:
    st.subheader("💡 語感調整建議")
    if st.session_state.is_analyzed:
        res = st.session_state.final_results
        if not res:
            st.success("✨ 經過掃描，這段文字非常符合台灣在地的語感。")
        else:
            st.warning(f"🔔 偵測到 {len(res)} 處建議調整的詞彙：")
            for item in res:
                # 檢查詞彙是否還存在於當前文字中
                if item['original'] in st.session_state.current_text:
                    with st.expander(f"📌 在地建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                        st.write(f"📘 **調整建議：** {item['reason']}")
                        if st.button(f"套用建議：{item['taiwan']}", key=f"btn_{item['original']}"):
                            apply_change(item['original'], item['taiwan'])
                            st.rerun()
    else:
        st.write("掃描完成後，建議調整的資訊會顯示於此。")
