import streamlit as st

# 1. 完整詞典：包含台灣語感、解釋、差異用法
TERM_DATABASE = {
    "視頻": {
        "tw": "影片",
        "diff": "台灣習慣稱「影片」，源於底片、電影片的傳統；大陸則常用「視頻」指稱頻率訊號。",
        "example": "例：這個影片的剪輯非常專業。"
    },
    "軟件": {
        "tw": "軟體",
        "diff": "台灣將 Software 譯為「軟體」，與硬體（Hardware）成對；大陸則慣用「件」字。",
        "example": "例：這套辦公軟體是免費下載的。"
    },
    "質量": {
        "tw": "品質",
        "diff": "大陸的「質量」兼具物理重量與 Quality 之意；台灣在形容產品優劣時僅使用「品質」。",
        "example": "例：這家餐廳的服務品質非常高。"
    },
    "優化": {
        "tw": "最佳化",
        "diff": "電腦科學中，台灣使用「最佳化」指代 Optimization；「優化」在台灣語感中較偏向對岸口語。",
        "example": "例：我們需要對資料庫進行最佳化處理。"
    },
    "內存": {
        "tw": "記憶體",
        "diff": "大陸稱 Memory 為「內存」；台灣則統一稱為「記憶體」。",
        "example": "例：這台筆電的記憶體不足，跑不動程式。"
    },
    "網絡": {
        "tw": "網路",
        "diff": "台灣慣用「路」字（如網際網路）；大陸則常用「絡」字。",
        "example": "例：目前的網路連線非常不穩定。"
    }
}

# 2. 頁面風格設定 (顯白、專業、精美卡片)
st.set_page_config(page_title="台灣語感轉換專家", layout="wide")

st.markdown("""
    <style>
    /* 全域顯白背景 */
    .stApp { background-color: #ffffff; }
    
    /* 轉換後的高亮文字 */
    .highlight {
        color: #d9534f;
        font-weight: bold;
        background-color: #fff5f5;
        padding: 2px 4px;
        border-radius: 4px;
    }
    
    /* 自動跳出的解釋卡片樣式 */
    .explanation-card {
        background-color: #f8f9fa;
        border-left: 6px solid #007bff;
        padding: 20px;
        margin-top: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #007bff;
        margin-bottom: 8px;
    }
    .card-diff {
        font-size: 0.95rem;
        color: #444;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 主介面
st.title("🇹🇼 台灣語感專家")
st.subheader("自動偵測大陸用語並提供用法解釋")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📥 原始文字")
    input_text = st.text_area("請在此貼上內容...", placeholder="例如：這個視頻的質量與軟件優化都很到位...", height=300)

with col2:
    st.markdown("### 📤 轉換結果")
    
    output_html = input_text
    found_terms = []
    
    if input_text:
        # 執行轉換並標記
        for cn, info in TERM_DATABASE.items():
            if cn in input_text:
                # 在顯示結果中高亮轉換後的詞
                output_html = output_html.replace(cn, f'<span class="highlight">{info["tw"]}</span>')
                found_terms.append(cn)
        
        # 渲染轉換後的 HTML 內容
        st.markdown(f"""
            <div style="background:#fff; padding:20px; border:1px solid #ddd; border-radius:10px; min-height:300px; line-height:1.8;">
                {output_html if output_html else "等待輸入中..."}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("請在左側輸入文字。")

# 4. 下方自動跳出的解釋區域
if found_terms:
    st.divider()
    st.markdown("### 💡 術語差異解析 (自動生成)")
    
    # 這裡就是你說的：自動根據右邊轉換的詞跳出卡片
    for term in found_terms:
        data = TERM_DATABASE[term]
        st.markdown(f"""
            <div class="explanation-card">
                <div class="card-title">🇨🇳 {term} ➔ 🇹🇼 {data['tw']}</div>
                <div class="card-diff">
                    <b>【用法差異】</b><br>{data['diff']}<br>
                    <span style="color: #28a745; font-size: 0.9em;">{data['example']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# 清除功能
if st.button("🧹 清除全部內容"):
    st.rerun()
