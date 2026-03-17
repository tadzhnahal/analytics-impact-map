from python:3.12-slim
workdir /app

copy requirements.txt .
run pip install --no-cache-dir -r requirements.txt
copy . .

cmd ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
