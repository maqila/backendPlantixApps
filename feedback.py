from fastapi import APIRouter, HTTPException, Form
from database import db_dependency
from sqlalchemy.sql import text
import pandas as pd
import sqlalchemy

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
)

@router.get("/")
async def get_feedbacks(db: db_dependency):
    with db.connection() as conn:
        data = pd.read_sql(
            sqlalchemy.text('SELECT * FROM public.feedback'),
            conn
        )
    if data.empty:
        raise HTTPException(status_code=404, detail="No feedbacks found")
    return {
        "status": 200,
        "msg": "Success Get Feedbacks",
        "data": data.to_dict('records')
    }

@router.post("/create")
async def create_feedback(db: db_dependency, user_id: int = Form(...), detection_id: int = Form(...), rating: int = Form(...), comments: str = Form(...)):
    try:
        # Menggunakan parameterisasi untuk menghindari SQL Injection
        sql = text('''
            INSERT INTO public."feedback" (user_id, detection_id, rating, comments)
            VALUES (:user_id, :detection_id, :rating, :comments)
        ''')
        db.execute(sql, {"user_id": user_id, "detection_id": detection_id, "rating": rating, "comments": comments})
        db.commit()
        return {
            "status": 201,
            "msg": "Feedback created successfully"
        }
    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@router.get("/get/{feedbackId}")
async def get_feedback_detail(feedbackId: int, db: db_dependency):
    with db.connection() as conn:
        data = pd.read_sql(
            sqlalchemy.text(
                f'SELECT * FROM public."feedback" WHERE id = {feedbackId}'
            ), conn
        )
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Feedback not found")
    return {
        "status": 200,
        "msg": "Success Generate Feedback Detail",
        "data": data.to_dict('records')
    }

@router.get("/user/{userId}")
async def get_feedbacks_by_user(userId: int, db: db_dependency):
    with db.connection() as conn:
        data = pd.read_sql(
            sqlalchemy.text(
                f'SELECT * FROM public."feedback" WHERE user_id = {userId}'
            ), conn
        )
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Feedback not found")
    return {
        "status": 200,
        "msg": "Success Generate Feedback list",
        "data": data.to_dict('records')
    }