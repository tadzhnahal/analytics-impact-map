from fastapi import FastAPI, HTTPException
from db import get_db_connection

app = FastAPI(title="Analytics Impact Map")

@app.get("/")
def root():
    return {"message": "бэк жив"}

@app.get("/health/db")
def health_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("select 1;")
        row = cur.fetchone()
        cur.close()
        conn.close()

        return {
            "status": "ok",
            "database": "connected",
            "result": row[0],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"db error: {e}")