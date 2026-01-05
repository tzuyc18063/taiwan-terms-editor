<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>本地數據管理系統</title>
    <style>
        /* 恢復你喜歡的乾淨顯白風格 */
        body { font-family: "Microsoft JhengHei", sans-serif; background-color: #ffffff; color: #333; margin: 0; padding: 50px; display: flex; justify-content: center; }
        .card { width: 100%; max-width: 500px; border: 1px solid #eee; padding: 20px; border-radius: 12px; shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h2 { border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; font-weight: 400; }
        .input-group { margin: 20px 0; display: flex; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; outline: none; }
        button { padding: 10px 20px; cursor: pointer; border-radius: 6px; border: none; transition: 0.3s; }
        .btn-add { background-color: #007bff; color: white; }
        .btn-add:hover { background-color: #0056b3; }
        ul { list-style: none; padding: 0; }
        li { background: #f9f9f9; margin-bottom: 8px; padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #007bff; }
        .btn-del { background-color: #ff4d4f; color: white; font-size: 12px; }
    </style>
</head>
<body>

<div class="card">
    <h2>數據清單</h2>
    
    <div class="input-group">
        <input type="text" id="itemInput" placeholder="請輸入內容...">
        <button class="btn-add" onclick="addItem()">新增</button>
    </div>

    <ul id="itemList"></ul>
</div>

<script>
    // 核心邏輯：直接讀取瀏覽器內部的存儲空間
    let storageKey = "my_local_data";

    function loadData() {
        const list = document.getElementById('itemList');
        const data = JSON.parse(localStorage.getItem(storageKey) || "[]");
        
        list.innerHTML = data.map((item, index) => `
            <li>
                <span>${item}</span>
                <button class="btn-del" onclick="deleteItem(${index})">刪除</button>
            </li>
        `).join('');
    }

    function addItem() {
        const input = document.getElementById('itemInput');
        if (!input.value.trim()) return;

        const data = JSON.parse(localStorage.getItem(storageKey) || "[]");
        data.push(input.value);
        localStorage.setItem(storageKey, JSON.stringify(data));
        
        input.value = '';
        loadData();
    }

    function deleteItem(index) {
        const data = JSON.parse(localStorage.getItem(storageKey) || "[]");
        data.splice(index, 1);
        localStorage.setItem(storageKey, JSON.stringify(data));
        loadData();
    }

    // 初始載入
    loadData();
</script>

</body>
</html>
