from flask import Flask, render_template_string, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = "data.json"

# 確保本地有資料檔
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 網頁 HTML 模板 (顯白、簡潔、不卡頓) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>快速本地管理系統</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background-color: #f4f4f9; }
        .container { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        input { padding: 8px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 8px 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #218838; }
        ul { list-style: none; padding: 0; margin-top: 20px; }
        li { padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }
        .delete-btn { background: #dc3545; padding: 3px 8px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>數據管理 (本地版)</h2>
        <input type="text" id="itemInput" placeholder="輸入名稱...">
        <button onclick="addItem()">新增</button>
        <ul id="itemList"></ul>
    </div>

    <script>
        // 初始化載入
        async function loadItems() {
            const res = await fetch('/api/data');
            const data = await res.json();
            const list = document.getElementById('itemList');
            list.innerHTML = data.map(item => `
                <li>
                    ${item.name} 
                    <button class="delete-btn" onclick="deleteItem(${item.id})">刪除</button>
                </li>
            `).join('');
        }

        async function addItem() {
            const input = document.getElementById('itemInput');
            if (!input.value) return;
            await fetch('/api/data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: input.value })
            });
            input.value = '';
            loadItems();
        }

        async function deleteItem(id) {
            await fetch(`/api/data/${id}`, { method: 'DELETE' });
            loadItems();
        }

        loadItems();
    </script>
</body>
</html>
"""

# --- 後端 API 路由 ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/data', methods=['POST'])
def add_data():
    data = load_data()
    new_item = {
        "id": len(data) + 1,
        "name": request.json.get("name")
    }
    data.append(new_item)
    save_data(data)
    return jsonify({"status": "success"})

@app.route('/api/data/<int:item_id>', methods=['DELETE'])
def delete_data(item_id):
    data = load_data()
    data = [i for i in data if i['id'] != item_id]
    save_data(data)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    print("網頁伺服器已啟動：http://127.0.0.1:5000")
    app.run(debug=True)
