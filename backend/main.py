from fastapi import FastAPI

app = FastAPI(title="Analytics Impact Map")

@app.get("/")
def root():
    return {"message": "бэк жив"}