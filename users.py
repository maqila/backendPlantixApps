from fastapi import APIRouter, HTTPException, Form, UploadFile, File, Request
from database import db_dependency
import uuid
import pandas as pd
import sqlalchemy
from pathlib import Path
import os

router = APIRouter(
    prefix='/users',
    tags=['users']
)

UPLOAD_DIRECTORY = "uploads/users"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)  # Create the directory if it doesn't exist

# Fungsi membuat Filename baru
def generate_new_filename(file, Id):
    """Generate a new filename based on a specific format."""
    file_extension = file.filename.split(".")[-1]  # Get the file extension
    new_filename = f"imagesUser{Id}{str(uuid.uuid4())[:8]}.{file_extension}"  # Create a new filename using UUID
    return new_filename

# Fungsi menyimpan file secara lokal
def save_file_locally(file: UploadFile, filename: str) -> str:
    """Save uploaded file locally and return its path."""
    file_path = Path(UPLOAD_DIRECTORY) / filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return str(file_path)

@router.get("/detail")
async def get_users_detail(userId: int, db: db_dependency):
    with db.connection() as conn:
        query = sqlalchemy.text(
            'SELECT * FROM public.users WHERE id = :userId'
        )
        data = pd.read_sql(query, conn, params={'userId': userId})

    if data.empty:
        raise HTTPException(status_code=404, detail=f"User with userId {userId} not found")

    return {
        "status": 200,
        "msg": "Success Get User Details",
        "data": data.to_dict('records')
    }

@router.put("/update{userId}")
async def update_user(db: db_dependency, userId: int, full_name: str = Form(...), profile_picture: UploadFile = File(...), request: Request):
    if profile_picture.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Invalid image file")

    new_filename = generate_new_filename(profile_picture, userId)
    picture_path = save_file_locally(profile_picture, new_filename)

    # Bangun URL lengkap untuk gambar profil
    base_url = str(request.base_url)  # Ambil URL dasar (misalnya: http://127.0.0.1:8000/)
    full_picture_url = f"{base_url}{picture_path}"  # Gabungkan URL dasar dengan path gambar

    with db.connection() as conn:
        # Check if the user exists
        existing_user_query = sqlalchemy.text(
            'SELECT * FROM public.users WHERE id = :userId'
        )
        existing_user = pd.read_sql(existing_user_query, conn, params={'userId': userId})

        if existing_user.empty:
            raise HTTPException(status_code=404, detail=f"User with userId {userId} not found")
        
        # Update user details
        update_query = sqlalchemy.text(
            'UPDATE public.users SET '
            '"full_name" = :full_name, '
            '"profile_picture_url" = :profile_picture_url '
            'WHERE id = :userId'
        )
        try:
            conn.execute(
                update_query,{
                    "full_name": full_name,
                    "profile_picture_url": full_picture_url,
                    "userId": userId
                    })
            conn.commit()
        except Exception as e:
            conn.rollback()  # Rollback transaksi jika terjadi kesalahan
            print("Error during update:", e)

        # Get updated user details
        updated_user_query = sqlalchemy.text(
            'SELECT * FROM public.users WHERE id = :userId'
        )
        updated_user = pd.read_sql(updated_user_query, conn, params={'userId': userId})

    return {
        "status": 200,
        "msg": f"User details updated successfully for userId {userId}",
        "data": updated_user.to_dict('records'),
        "picture_url": full_picture_url
    }
