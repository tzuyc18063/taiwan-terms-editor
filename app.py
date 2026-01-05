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

# --- 2. 終極鐵腕硬核清單 (只要出現就強制抓取，不聽 AI 解釋) ---
# 這裡加入了「套路」、「走心」等詞彙
HARDCORE_RULES = {
    "套路": {"tw": "花招 / 陷阱 / 慣用手段", "reason": "「套路」原指武術動作，在大陸流行語中指精心策劃的應對方式；台灣道地說法多用「花招」、「話術」或「手段」。", "example": "這都是商家的行銷花招。"},
    "走心": {"tw": "用心 / 認真 / 觸動內心", "reason": "大陸語境中「走心」指用心或有感觸；台灣傳統語意中「走心」反而有「偏離本意、在意、鑽牛角尖」的意思，建議依照語境更換。", "example": "這部電影的劇情非常動人。"},
    "視頻": {"tw": "影片", "reason": "台灣在地習慣稱為「影片」。", "example": "這部影片剪輯得很專業。"},
    "很火": {"tw": "很紅 / 大受歡迎", "reason": "台灣習慣用「很紅」，「很火」是典型大陸用語。", "example": "這款手遊最近在台灣非常紅。"},
    "牛逼": {"tw": "厲害 / 強", "reason": "大陸北方口語，在台灣極不自然且略顯粗俗。", "example": "你的技術真的太厲害了。"},
    "質量": {"tw": "品質", "reason": "形容物品優劣請務必用「品質」。", "example": "這台筆電的硬體品質很好。"},
    "優化": {"tw": "最佳化 / 改善", "reason": "電腦領域慣用「最佳化」，生活用語用「改善」。", "example": "系統效能需要進一步最佳化。"}
}

# 狀態管理
if 'current_text' not in st.session_state: st.session_state.current_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False
if 'final_results' not in st.session_state: st.session_state.final_results = []

def apply_change(old, new):
    st.session_state.current_text = st.session_state.current_text.replace(old, new)
    st.toast(f"✅ 已修正為：{new}")

# --- 3. 雙層審核邏輯 ---
def total_enforcement(text):
    results = []
    
    # 第一層：強制攔截 (鐵腕過濾，不經 AI)
    for cn, info in HARDCORE_RULES.items():
        if cn in text:
            results.append({
                "original": cn,
                "taiwan": info["tw"],
                "reason": f"【硬核偵測】{info['reason']}",
                "example": info["example"]
            })
    
    # 第二層：AI 深度掃描 (挖掘其他漏網之魚)
    prompt = f"""
    你現在是一位極其嚴厲的台灣語感檢察官。
    請找出文字中不符合台灣用語習慣的大陸用語或流行語。
    待分析文字："{text}"
    請務必回傳 JSON 陣列，若無發現則回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
            for item in ai_data:
                # 避免與硬核名單重複
                if not any(r['original'] == item['original'] for r in results):
                    results.append(item)
    except:
        pass
    return results

# --- 4. 介面呈現 ---
st.title("📱 語感守護者：終極鐵腕模式")
st.markdown("### 🚫 絕不姑息大陸用語，徹底守護在地語感")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("📝 輸入文字")
    u_input = st.text_area("請輸入待檢查的內容：", height=200, 
                           value="這個套路真的很火，視頻質量牛逼。", key="u_input")
    
    if st.button("🚀 執行終極偵測", use_container_width=True):
        with st.spinner("檢察官正在嚴格執法中..."):
            st.session_state.current_text = u_input
            st.session_state.final_results = total_enforcement(u_input)
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.info("**預覽內容：**")
        st.code(st.session_state.current_text, language=None)

with c2:
    st.subheader("🤳 診斷報告與建議")
    
    if st.session_state.is_analyzed:
        res = st.session_state.final_results
        
        if not res:
            st.success("✨ 經過鐵腕查緝，文字完全符合台灣在地語感。")
        else:
            st.error(f"🚨 抓到 {len(res)} 處違規用法！")
            for item in res:
                if item['original'] in st.session_state.current_text:
                    with st.expander(f"📌 強制修正：{item['original']} ➔ {item['taiwan']}", expanded=True):
                        st.write(f"🇹🇼 **建議替換：** {item['taiwan']}")
                        st.write(f"💡 **差異解析：** {item['reason']}")
                        st.caption(f"📖 **道地範例：** {item['example']}")
                        
                        if st.button(f"接受修正：{item['taiwan']}", key=f"btn_{item['original']}"):
                            apply_change(item['original'], item['taiwan'])
                            st.rerun()
    else:
        st.write("請輸入文字開始掃描。")

# 底部功能
if st.button("🧹 清除並重置"):
    st.session_state.current_text = ""
    st.session_state.is_analyzed = False
    st.session_state.final_results = []
    st.rerun()
