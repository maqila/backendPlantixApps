from fastapi import APIRouter, HTTPException, Form
from database import db_dependency
from model import Plant
from sqlalchemy.sql import text
import pandas as pd
import sqlalchemy

router = APIRouter(
    prefix="/plant",
    tags=["plant"],
)

@router.post("/create")
async def create_plant(db: db_dependency, userId: int = Form(...), nama: str = Form(...)):
    new_plant = Plant(
        user_id = userId,
        nama = nama
    )
    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)
    return{
        "status": 200,
        "msg": "Feedback created successfully",
        "data": {
            "id": new_plant.id,
            "user_id": new_plant.user_id,
            "nama": new_plant.nama
        }
    }

@router.get("/")
async def get_plant(db: db_dependency):
    with db.connection() as conn:
        data = pd.read_sql(
            sqlalchemy.text('SELECT * FROM public.plant'),
            conn
        )
    if data.empty:
        raise HTTPException(status_code=404, detail="No plants found")
    return {
        "status": 200,
        "msg": "Success Get Plant",
        "data": data.to_dict('records')
    }

@router.get("/user/{userId}")
async def get_plant_by_user(userId: int, db: db_dependency):
    with db.connection() as conn:
        data = pd.read_sql(
            sqlalchemy.text(
                f'SELECT * FROM public.plant WHERE user_id = {userId}'
            ), conn
        )
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Plant not found")
    return {
        "status": 200,
        "msg": "Success Generate User Plant List",
        "data": data.to_dict('records')
    }

@router.get("/list/{userId}")
async def get_view(userId: int, db: db_dependency):
    with db.connection() as conn:
        data = pd.read_sql(
            sqlalchemy.text(
                f'SELECT * FROM public.view_list WHERE user_id = {userId}'
            ), conn
        )
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Plant not Found")
    return{
        "status": 200,
        "msg": "Success Generate User List Plant",
        "data": data.to_dict('records')
    }