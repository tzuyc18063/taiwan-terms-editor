# --- 更新後的混合分析邏輯 ---
def combined_analyze(text):
    results = []
    
    # 第一步：靜態名單比對 (維持不變，確保速度)
    for cn, info in FAST_LIST.items():
        if cn in text:
            results.append({
                "original": cn,
                "taiwan": info["tw"],
                "reason": f"【即時偵測】{info['reason']}",
                "example": f"這段{info['tw'].split(' / ')[0]}拍得很專業。"
            })
    
    # 第二步：強化版 AI 補足 (針對像「蛐蛐」這類流行動詞)
    prompt = f"""
    你是一位台灣語感專家。請分析以下文字中「不符合台灣在地口語習慣」的詞彙。
    特別注意：除了名詞，也要找出不道地的「動詞」、「形容詞」或「網路流行黑話」（例如：蛐蛐、哈基米、家人們等）。
    
    待分析文字："{text}"
    
    【回傳規範】：
    1. 若發現類似「蛐蛐」（背後說壞話）這類的用法，請提供台灣對應詞（如：碎嘴、說閒話、嚼舌根）。
    2. 排除已在名單中的詞彙：{list(FAST_LIST.keys())}。
    3. 嚴格以 JSON 陣列格式回傳，格式為：[{{"original": "...", "taiwan": "...", "reason": "..."}}]。
    4. 若無發現請回傳 []。
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            ai_data = json.loads(match.group())
            for item in ai_data:
                if not any(r['original'] == item['original'] for r in results):
                    results.append(item)
    except:
        pass
        
    return results
