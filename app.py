def run_sync_analysis(text):
    if not text.strip(): return
    
    # 1. 修正模型名稱與安全設定
    try:
        # 嘗試使用更穩定的模型路徑名稱
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        
        prompt = f'你是一個繁體中文語感專家。找出文字中的中國用語。文字："{text}"。格式：原詞|建議|解釋'
        
        response = model.generate_content(prompt)
        
        # 檢查回應是否有效
        if not response.text:
            st.error("AI 回傳內容為空")
            return
            
        ai_res = []
        for line in response.text.strip().split('\n'):
            if "|" in line:
                p = line.split("|")
                if len(p) >= 3:
                    ai_res.append({"w": p[0].strip(), "r": p[1].strip(), "e": p[2].strip()})
        st.session_state.res_list = ai_res
        
        # 2. 💥 強制同步區 💥
        if ai_res:
            st.info("🔄 AI 辨識成功，正在連線 Google Sheets...")
            try:
                # 建立連線
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # 指定工作表名稱為 Sheet1
                df = conn.read(worksheet="Sheet1", ttl=0)
                
                new_data = pd.DataFrame([
                    {'original': i['w'], 'replacement': i['r'], 'explanation': i['e'], 'title': 'AI學習', 'suggestion': i['r']} 
                    for i in ai_res
                ])
                
                # 合併並去重
                if df is not None and not df.empty:
                    updated_df = pd.concat([df, new_data]).drop_duplicates(subset=['original'], keep='last')
                else:
                    updated_df = new_data
                
                # 執行寫入
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success("✅ 雲端同步成功！資料已寫入 Sheet1。")
                
            except Exception as e:
                st.error(f"❌ 雲端寫入動作失敗：{e}")
                st.info("提示：請檢查 Secrets 中的 private_key 是否為單引號包覆的一整行字串。")

    except Exception as ai_e:
        # 如果最新版模型也失敗，嘗試降級模型名稱
        st.warning(f"偵測到模型存取問題，正在嘗試備用方案...")
        try:
            model = genai.GenerativeModel('gemini-pro')
            # ... (後續邏輯同上)
        except:
            st.error(f"AI 服務連線失敗：{ai_e}")
