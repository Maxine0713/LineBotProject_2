# 建立虛擬環境（建議）
python -m venv venv
# 啟用虛擬環境（建議）
Linux / macOS: source venv/bin/activate  
Windows: venv\Scripts\activate

# 安裝依賴套件
pip install -r requirements.txt

# 啟動 FastAPI 應用：
python -m uvicorn main:app --reload --host 0.0.0.0 --port 5000