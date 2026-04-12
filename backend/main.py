from fastapi import FastAPI, HTTPException

from db import get_db_connection
from schemas import ComponentCreate, ComponentOut, DependencyCreate, DependencyOut

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

@app.post("/dependencies", response_model=DependencyOut)
def create_dependency(dependency: DependencyCreate):
    if dependency.source_component_id == dependency.target_component_id:
        raise HTTPException(status_code=400, detail="component cannot depend on itself")

    if dependency.dependency_type not in ["hard", "soft"]:
        raise HTTPException(status_code=400, detail="dependency_type must be hard or soft")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "select id from components where id = %s;",
            (dependency.source_component_id,)
        )
        source_row = cur.fetchone()

        cur.execute(
            "select id from components where id = %s;",
            (dependency.target_component_id,)
        )
        target_row = cur.fetchone()

        if not source_row or not target_row:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="one or both components do not exist")

        cur.execute(
            """
            insert into dependencies (source_component_id, target_component_id, dependency_type)
            values (%s, %s, %s)
            returning id, source_component_id, target_component_id, dependency_type;
            """,
            (
                dependency.source_component_id,
                dependency.target_component_id,
                dependency.dependency_type,
            ),
        )

        row = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        return {
            "id": row[0],
            "source_component_id": row[1],
            "target_component_id": row[2],
            "dependency_type": row[3],
        }

    except HTTPException:
        raise

    except Exception as e:
        error_text = str(e).lower()

        if "duplicate key value" in error_text:
            raise HTTPException(status_code=400, detail="this dependency already exists")

        raise HTTPException(status_code=500, detail=f"db error: {e}")

@app.get("/dependencies", response_model=list[DependencyOut])
def get_dependencies():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """
            select id, source_component_id, target_component_id, dependency_type
            from dependencies
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
                    "source_component_id": row[1],
                    "target_component_id": row[2],
                    "dependency_type": row[3],
                }
            )
            
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"db error: {e}")

