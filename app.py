import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import pandas as pd

# --- 1. 頁面設定 ---
st.set_page_config(page_title="語感專家：暴力辨識版", page_icon="🧠", layout="wide")

# 初始化 Session
if 'f_text' not in st.session_state: st.session_state.f_text = ""
if 'res_list' not in st.session_state: st.session_state.res_list = []

# --- 2. 核心修正動作 ---
def do_fix(old_w, new_w):
    st.session_state.f_text = st.session_state.f_text.replace(old_w, new_w)
    st.toast(f"✅ 已修正：{old_w}")

# --- 3. 核心辨識邏輯 ---
def power_analysis(text):
    if not text.strip(): return
    
    # 強制手動偵測清單 (保險絲：AI 萬一失靈，這些詞也一定會跳出來)
    fallback_rules = [
        {"w": "視頻", "r": "影片", "e": "源自中國，台灣習慣稱為『影片』。"},
        {"w": "質量", "r": "品質", "e": "源自中國，台灣指物理量，品質才指好壞。"},
        {"w": "優化", "r": "改善", "e": "源自中國，台灣多用『改善』、『提升』或『最佳化』。"}
    ]
    
    # 建立手動結果
    manual_results = [r for r in fallback_rules if r['w'] in text]
    
    try:
        # 關閉所有 AI 安全過濾，避免它拒絕回傳
        safe = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safe)
        
        prompt = f"""你是一個台灣語感專家。找出以下文字中的中國用語（如：軟件、硬盤、視頻、質量、優化、內卷）。
        文字："{text}"
        請嚴格按格式回傳（不要廢話）：原詞|建議|解釋（解釋中『源自大陸』改為『源自中國』）"""
        
        response = model.generate_content(prompt)
        ai_results = []
        if response.text:
            for line in response.text.strip().split('\n'):
                if "|" in line:
                    p = line.split("|")
                    if len(p) >= 3:
                        ai_results.append({"w": p[0].strip(), "r": p[1].strip(), "e": p[2].strip()})
        
        # 合併手動與 AI 結果並去重
        all_res = {item['w']: item for item in (manual_results + ai_results)}.values()
        st.session_state.res_list = list(all_res)
        
        # 背景寫入雲端 (不影響顯示)
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(ttl="1s")
            new_data = pd.DataFrame([{'original': i['w'], 'replacement': i['r'], 'explanation': i['e']} for i in st.session_state.res_list])
            conn.update(data=pd.concat([df, new_data]).drop_duplicates(subset=['original'], keep='last'))
        except: pass

    except Exception as e:
        st.session_state.res_list = manual_results # AI 爆掉時至少還有手動保險

# --- 4. 介面 ---
st.title("🧠 語感專家：暴力辨識版")

c1, c2 = st.columns([1, 1.2])

with c1:
    user_in = st.text_area("📝 輸入文字：", height=200, key="main_in")
    if st.button("🚀 啟動暴力辨識", use_container_width=True):
        st.session_state.f_text = user_in
        power_analysis(user_in)
        st.rerun()

    if st.session_state.f_text:
        st.markdown("---")
        st.subheader("📋 修正結果")
        st.code(st.session_state.f_text, language=None)

with c2:
    st.subheader("🤳 辨識卡片")
    has_any = False
    for i, item in enumerate(st.session_state.res_list):
        if item['w'] in st.session_state.f_text:
            has_any = True
            with st.expander(f"📌 偵測到：{item['w']}", expanded=True):
                st.write(f"🔍 **解釋：** {item['e']}")
                st.button(f"👉 修正為「{item['r']}」", key=f"b_{i}", on_click=do_fix, args=(item['w'], item['r']), use_container_width=True)
    
    if not has_any and st.session_state.f_text:
        st.success("🎉 暫無建議")
