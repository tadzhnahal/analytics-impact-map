from fastapi import FastAPI, HTTPException

from db import get_db_connection
from schemas import ComponentCreate, ComponentOut

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

@app.post("/components", response_model=ComponentOut)
def create_component(component: ComponentCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            insert into components (name, component_type, description)
            values (%s, %s, %s)
            returning id, name, component_type, description;
            """,
            (component.name, component.component_type, component.description),
        )

        row = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        return {
            "id": row[0],
            "name": row[1],
            "component_type": row[2],
            "description": row[3],
        }

    except Exception as e:
        error_text = str(e).lower()

        if "duplicate key value" in error_text:
            raise HTTPException(status_code=400, detail="component with this name already exists")

        raise HTTPException(status_code=500, detail=f"db error: {e}")

@app.get("/components", response_model=list[ComponentOut])
def get_components():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            select id, name, component_type, description
            from components
            order by id
            """
        )

        rows = cur.fetchall()

        cur.close()
        conn.close()

        result = []

        for row in rows:
            result.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "component_type": row[2],
                    "description": row[3],
                }
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"db error: {e}")
