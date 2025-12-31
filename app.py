import streamlit as st
import google.generativeai as genai
import json
import re
import os

# --- 1. 配置與初始化 ---
st.set_page_config(page_title="語感專家：智慧進化版", page_icon="🧠", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

DB_FILE = "knowledge_base.json"

# --- 2. 資料庫操作函數 (永久儲存) ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_to_db(new_cards):
    db = load_db()
    for card in new_cards:
        # 以原詞作為 Key，若資料庫沒有才存入，或更新舊資料
        db[card['original']] = card
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# --- 3. 智慧辨識引擎 (聯網搜尋 + 知識整合) ---
def start_smart_analysis(text):
    if not text.strip(): return []
    
    # 載入現有資料庫作為背景知識
    local_db = load_db()
    known_terms = list(local_db.keys())
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{"google_search_retrieval": {}}] 
    )
    
    prompt = f"""
    任務：你是兩岸用語校正專家。
    待分析文字："{text}"
    目前已知的本地詞庫：{known_terms}
    
    要求：
    1. 分析文字中不符合台灣語感的詞。
    2. 如果遇到詞庫中沒有的新詞（如：內卷、內耗），請務必使用 Google 搜尋確認台灣最在地的說法。
    3. 台灣不說「好皮」，必須改為「好皮膚」。
    
    請回傳 JSON 列表：
    [
      {{"original": "原詞", "replacement": "台灣建議", "title": "百科標題", "explanation": "解釋", "suggestion": "建議"}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            new_cards = json.loads(json_match.group(0))
            # 【關鍵點】查完後自動存入資料庫，實現永久記住
            save_to_db(new_cards)
            return new_cards
        return []
    except:
        return []

# --- 4. UI 介面 ---
st.title("🧠 語感專家：具備永久記憶的 AI")
st.caption("AI 查到的新詞會自動存入本地資料庫，下次辨識將直接調用。")

col_left, col_right = st.columns([1, 1.2])

# 初始化狀態
if 'processed_text' not in st.session_state: st.session_state.processed_text = ""
if 'is_analyzed' not in st.session_state: st.session_state.is_analyzed = False

with col_left:
    st.subheader("📝 文字輸入")
    u_input = st.text_area("輸入任何文字：", height=200, value="職場內卷太嚴重，這視頻很火。")
    
    if st.button("🚀 啟動進化辨識", use_container_width=True):
        st.session_state.processed_text = u_input
        with st.spinner("AI 正在搜尋並更新知識庫..."):
            start_smart_analysis(u_input) # 執行並儲存
            st.session_state.is_analyzed = True

    if st.session_state.is_analyzed:
        st.code(st.session_state.processed_text, language=None)
        
    # 顯示目前資料庫統計
    db_size = len(load_db())
    st.write(f"📊 目前資料庫已永久記住 `{db_size}` 個用語差異。")

with col_right:
    st.subheader("🤳 智慧百科 (含永久記憶)")
    if st.session_state.is_analyzed:
        db = load_db()
        current_text = st.session_state.processed_text
        
        # 從資料庫中抓取文字中存在的詞
        found = False
        for word, card in db.items():
            if word in current_text:
                found = True
                with st.expander(f"📌 記憶百科：{word}", expanded=True):
                    st.markdown(f"### {card['title']}")
                    st.write(card['explanation'])
                    if st.button(f"👉 修正為「{card['replacement']}」", key=f"fix_{word}"):
                        st.session_state.processed_text = current_text.replace(word, card['replacement'])
                        st.rerun()
        if not found:
            st.success("🎉 目前文字查無非在地用語！")
