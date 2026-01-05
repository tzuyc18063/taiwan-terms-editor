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
    st.error("❌ 系統提示：請檢查 API 金鑰設定。")
    st.stop()

# --- 2. 靜態必殺名單 (秒出結果) ---
# 這些詞彙不經過 AI，直接在本地端比對，速度最快
FAST_LIST = {
    "套路": {"tw": "花招 / 陷阱", "reason": "台灣道地說法通常使用「花招」或「手段」會更自然。"},
    "視頻": {"tw": "影片", "reason": "台灣在地習慣稱為「影片」。"},
    "很火": {"tw": "很紅 / 熱門", "reason": "台灣習慣用「很紅」或「大受歡迎」來形容。"},
    "牛逼": {"tw": "厲害 / 強", "reason": "建議使用「厲害」或「超強」會更親切且道地。"},
    "質量": {"tw": "品質", "reason": "形容物品優劣時，台灣習慣使用「品質」一詞。"},
    "優化": {"tw": "最佳化 / 改善", "reason": "科技領域稱「最佳化」，生活語法建議使用「改善」。"},
    "反饋": {"tw": "回饋", "reason": "台灣習慣使用「回饋」來指代意見反應。"},
    "走心": {"tw": "用心 / 認真", "reason": "「走心」在台灣有時帶有「在意」的負面含意，建議依語境調整。"}
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'final_results' not in st.session_state: st.session_state.final_results = []
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

def apply_change(old, new):
    target_new = new.split(' / ')[0]
    st.session_state.current_text = st.session_state.current_text.replace(old, target_new)
    st.toast(f"✅ 已更新：{old} ➔ {target_new}")

# --- 3. 混合分析邏輯 ---
def combined_analyze(text):
    results = []
    
    # 第一步：立即從靜態名單找 (零延遲)
    for cn, info in FAST_LIST.items():
        if cn in text:
            results.append({
                "original": cn,
                "taiwan": info["tw"],
                "reason": f"【即時偵測】{info['reason']}",
                "example": f"這段{info['tw'].split(' / ')[0]}拍得很專業。"
            })
    
    # 第二步：呼叫 AI 補足名單外的內容
    prompt = f"""
    你是一位台灣語感顧問。請找出文字中除了 {list(FAST_LIST.keys())} 以外，
    其他不符合台灣在地習慣的詞彙（如大陸流行語）。
    文字："{text}"
    請嚴格以 JSON 陣列格式回傳，若無則回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
            for item in ai_data:
                # 避免重複
                if not any(r['original'] == item['original'] for r in results):
                    results.append(item)
    except:
        pass # AI 若超時或失敗，至少還有靜態名單的結果
        
    return results

# --- 4. 介面呈現 ---
st.title("📱 語感守護者：混合偵測模式")
st.markdown("#### 結合「即時清單」與「AI 大數據」，兼顧速度與深度")

c1, c2 = st.columns([1, 1.2])

with c1:
    with st.container():
        st.subheader("📝 輸入內容")
        u_input = st.text_area("請在此輸入文字：", height=250, 
                               value="這個套路真的很火，視頻質量牛逼，需要優化一下。", key="u_input")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 執行語感掃描", use_container_width=True):
                st.session_state.current_text = u_input
                # 執行分析
                with st.spinner("正在進行深度語感分析..."):
                    st.session_state.final_results = combined_analyze(u_input)
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

with c2:
    st.subheader("💡 語感調整建議")
    if st.session_state.is_analyzed:
        active_results = [r for r in st.session_state.final_results if r['original'] in st.session_state.current_text]
        
        if not active_results:
            st.success("✨ 文字目前非常符合台灣在地的語感。")
        else:
            if st.button("🪄 一鍵套用所有建議", use_container_width=True):
                for item in active_results:
                    st.session_state.current_text = st.session_state.current_text.replace(item['original'], item['taiwan'].split(' / ')[0])
                st.session_state.final_results = []
                st.rerun()
                
            st.warning(f"🔔 發現 {len(active_results)} 處建議調整：")
            for item in active_results:
                with st.expander(f"📌 {item['original']} ➔ {item['taiwan']}", expanded=True):
                    st.write(f"📘 **調整建議：** {item['reason']}")
                    if st.button(f"套用此項：{item['taiwan']}", key=f"btn_{item['original']}"):
                        apply_change(item['original'], item['taiwan'])
                        st.rerun()
    else:
        st.write("等待掃描結果...")
