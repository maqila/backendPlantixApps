from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import auth
import users
import detection
import feedback
import plant

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plant.router)
app.include_router(detection.router)
app.include_router(feedback.router)

@app.get("/")
def read_root():
    return {"API" : "Plantix"}

# Path direktori untuk menyimpan file
UPLOADS_DIRECTORY = "uploads"
if not os.path.exists(UPLOADS_DIRECTORY):
    os.makedirs(UPLOADS_DIRECTORY)

# Tambahkan rute untuk melayani file statis
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIRECTORY), name="uploads")