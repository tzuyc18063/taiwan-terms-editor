import streamlit as st
import json
import os

# 1. 設定檔案路徑
DATA_FILE = "terms_data.json"

# 2. 定義讀取與儲存邏輯 (純本地，不連雲端)
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 3. 網頁頁面設定
st.set_page_config(page_title="台灣術語編輯器", layout="centered")
st.title("🇹🇼 台灣術語編輯器")
st.write("目前為本地存儲模式（不使用雲端資料庫）")

# 初始化數據
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# 4. 輸入介面 (修正後的表單元件)
with st.form("add_form", clear_on_submit=True):
    new_term = st.text_input("輸入新術語")
    # 這裡修正為正確的函式：st.form_submit_button
    submitted = st.form_submit_button("新增術語")
    
    if submitted and new_term:
        st.session_state.data.append(new_term)
        save_data(st.session_state.data)
        st.success(f"已儲存: {new_term}")
        st.rerun()

# 5. 顯示列表
st.divider()
st.subheader("現有術語列表")

if not st.session_state.data:
    st.info("目前沒有資料")
else:
    # 使用索引來處理刪除，避免列表變動錯誤
    for i, term in enumerate(st.session_state.data):
        cols = st.columns([0.8, 0.2])
        cols[0].write(f"{i+1}. {term}")
        # 為每個刪除按鈕建立唯一的 Key
        if cols[1].button("刪除", key=f"btn_{i}"):
            st.session_state.data.pop(i)
            save_data(st.session_state.data)
            st.rerun()
