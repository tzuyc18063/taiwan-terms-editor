import json
import os

class SimpleSystem:
    def __init__(self, filename="data_storage.json"):
        self.filename = filename
        self.data = self._load_data()

    def _load_data(self):
        """從本地讀取 JSON 檔案，如果不存在則回傳空列表"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_data(self):
        """將目前數據儲存到本地檔案"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def add_item(self, name, category, value):
        """新增一筆資料"""
        new_entry = {
            "id": len(self.data) + 1,
            "name": name,
            "category": category,
            "value": value
        }
        self.data.append(new_entry)
        self.save_data()
        print(f"✅ 已成功加入：{name}")

    def list_items(self):
        """顯示所有資料"""
        if not self.data:
            print("目前沒有任何記錄。")
            return
        
        print("\n" + "="*30)
        print(f"{'ID':<5} {'名稱':<10} {'類別':<10} {'數值':<5}")
        print("-" * 30)
        for item in self.data:
            print(f"{item['id']:<5} {item['name']:<10} {item['category']:<10} {item['value']:<5}")
        print("="*30 + "\n")

    def delete_item(self, item_id):
        """根據 ID 刪除資料"""
        initial_len = len(self.data)
        self.data = [item for item in self.data if item['id'] != item_id]
        
        if len(self.data) < initial_len:
            self.save_data()
            print(f"🗑️ 已刪除 ID: {item_id}")
        else:
            print(f"⚠️ 找不到 ID: {item_id}")

# --- 互動測試區 ---
if __name__ == "__main__":
    system = SimpleSystem()

    # 1. 範例新增
    system.add_item("測試項目A", "辦公", 100)
    system.add_item("測試項目B", "個人", 50)

    # 2. 顯示清單
    print("當前儲存的資料：")
    system.list_items()

    # 3. 測試刪除 (可選)
    # system.delete_item(1)
