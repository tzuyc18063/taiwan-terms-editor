import streamlit as st
import json
import os

# 1. 台灣語感轉換字典 (這就是你之前覺得不錯的核心)
TAIWAN_TERMS = {
    "視頻": "影片",
    "軟件": "軟體",
    "硬盤": "硬碟",
    "質量": "品質",
    "優化": "最佳化",
    "支持": "支援",
    "菜單": "選單",
    "激活": "啟用",
    "打印": "列印",
    "實時": "即時"
}

def translate_to_taiwan(text):
    """將內容依照字典轉換為台灣語感"""
    for cn, tw in TAIWAN_TERMS.items():
        text = text.replace(cn, tw)
    return text

# 2. 頁面設定
st.set_page_config(page_title="台灣語感轉換器", layout="centered")
st.title("🇹🇼 台灣語感轉換器")
st.write("輸入文字，自動轉換為台灣在地用語")

# 3. 轉換區
input_text = st.text_area("請輸入原始文字 (例如：這個視頻的質量很高)", height=150)

if st.button("立即轉換語感"):
    if input_text:
        result = translate_to_taiwan(input_text)
        st.subheader("轉換結果：")
        st.success(result)
        st.code(result) # 方便你一鍵複製
    else:
        st.warning("請先輸入文字")

# 4. 術語對照表 (讓你知道目前支援哪些轉換)
with st.expander("查看目前支援的術語對照"):
    cols = st.columns(2)
    cols[0].write("**原始詞彙**")
    cols[1].write("**台灣語感**")
    for cn, tw in TAIWAN_TERMS.items():
        c1, c2 = st.columns(2)
        c1.text(cn)
        c2.text(tw)
