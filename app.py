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
    st.error("❌ 系統提示：請確認 API 金鑰設定是否正確。")
    st.stop()

# --- 2. 在地語感資料庫 ---
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
    # 處理建議詞中有斜線的情況，預設取第一個建議
    target_new = new.split(' / ')[0]
    st.session_state.current_text = st.session_state.current_text.replace(old, target_new)
    st.toast(f"✅ 已更新：{old} ➔ {target_new}")

def apply_all_changes():
    for item in st.session_state.final_results:
        old = item['original']
        new = item['taiwan'].split(' / ')[0]
        if old in st.session_state.current_text:
            st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast("✅ 已套用所有語感建議")
    st.session_state.final_results = [] # 清空建議列表

def heavy_analyze(text):
    results = []
    for cn, info in HARDCORE_RULES.items():
        if cn in text:
            results.append({"original": cn, "taiwan": info["tw"], "reason": info["reason"]})
    
    prompt = f"你是一位台灣語感顧問。請找出文字中在台灣較不常見的詞彙並提供建議。文字：{text}。請僅回傳 JSON 陣列。"
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

    if st.session_state.is_analyzed:
        st.write("---")
        st.subheader("📋 修正後的文字")
        st.code(st.session_state.current_text, language=None)
        st.caption("💡 點擊右上方圖示即可快速複製文字。")

with c2:
    st.subheader("💡 語感調整建議")
    if st.session_state.is_analyzed:
        # 過濾掉已經不存在於文字中的建議（可能已被手動刪除或取代）
        active_results = [r for r in st.session_state.final_results if r['original'] in st.session_state.current_text]
        
        if not active_results:
            st.success("✨ 這段文字目前非常符合台灣在地的語感。")
        else:
            # 「一鍵套用全部」按鈕放在最上方
            if st.button("🪄 套用全部建議", use_container_width=True, type="primary"):
                apply_all_changes()
                st.rerun()
                
            st.warning(f"🔔 偵測到 {len(active_results)} 處建議調整的詞彙：")
            for item in active_results:
                with st.expander(f"📌 在地建議：{item['original']} ➔ {item['taiwan']}", expanded=True):
                    st.write(f"📘 **調整建議：** {item['reason']}")
                    if st.button(f"個別套用：{item['taiwan']}", key=f"btn_{item['original']}"):
                        apply_change(item['original'], item['taiwan'])
                        st.rerun()
    else:
        st.write("掃描後將在此顯示調整建議。")
