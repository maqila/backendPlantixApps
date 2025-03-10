from fastapi import APIRouter, HTTPException, Form, UploadFile, File, Request
from database import db_dependency
from model import UserDetection as Detection, Plant
from PIL import Image
import uuid
import pandas as pd
import sqlalchemy
import numpy as np
import joblib
from pathlib import Path
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Menghilangkan INFO dan WARNING
import tensorflow as tf

router = APIRouter(
    prefix='/detection',
    tags=['detection']
)

UPLOAD_DIRECTORY = "uploads/detections"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)  # Create the directory if it doesn't exist

# Fungsi membuat Filename baru
def generate_new_filename(file, Id):
    """Generate a new filename based on a specific format."""
    file_extension = file.filename.split(".")[-1]  # Get the file extension
    new_filename = f"imagesDetection{Id}{str(uuid.uuid4())[:8]}.{file_extension}"  # Create a new filename using UUID
    return new_filename

# Fungsi menyimpan file secara lokal
def save_file_locally(file: UploadFile, filename: str) -> str:
    """Save uploaded file locally and return its path."""
    file_path = Path(UPLOAD_DIRECTORY) / filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return str(file_path)

# Fungsi untuk preprocess gambar
def preprocess_image(image, target_size):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = np.array(image) / 255.0
    image = np.expand_dims(image, axis=0)
    return image

# Load the trained model
model = tf.keras.models.load_model('updated_plant_disease_model.keras')

# Load the LabelEncoder pkl file
label_encoder = joblib.load('updated_label_encoder.pkl')

# Data information dictionary
data_info = {
    'Bacteria': {
        'symptoms': "Daun menguning di sisi daun;Terdapat bercak atau berwarna gelap di sekitar area menguning;Lesi bermata hitam;Bintik-bintik cokelat dengan lingkaran cahaya kuning;Daun kering, layu dan rontok",
        'cause': "Kelembapan Tanah tidak tepat, terlalu banyak air;Kekurangan Nutrisi, salah satunya adalah nitrogen;Cahaya yang tidak sesuai (terlalu banyak terkena cahaya matahari langsung atau kurang terkena matahari);Infeksi bakteri",
        'treatment': "Menyiram tanaman ketika atas tanah sekitar 2-3 inci mulai kering.;Berikan bubuk yang seimbang sesuai dengan kebutuhan tanaman.;Tempatkan tanaman di lokasi yang tidak langsung terkena cahaya matahari.;Menyemprot daun dengan larutan air sabun atau obat pengusir serangga.;Jaga kebersihan tanah dan sterilisasi alat yang digunakan."
    },
    'Fungus': {
        'symptoms': "Daun menggulung;Munculnya bercak berwarna coklat, kuning, hitam atau abu-abu pada daun.;Tanaman layu meskipun telah disiram dengan cukup.",
        'cause': "Tanaman Kekurangan Nutrisi;Kelembaban tinggi dikarenakan seringnya menyiram tanaman;Kurangnya sirkulasi udara;Tanah atau media tanam terinfeksi jamur;Menyebar melalui serangga",
        'treatment': "Menggunakan fungisida dengan dosis yang tepat dan sesuai;Siram tanaman pada pagi hari, hindari menyirami tanaman terlalu sering.;Sterilisasi alat yang digunakan dalam merawat tanaman.;Sediakan tempat penanaman yang terkena matahari, memiliki drainase yang baik serta memiliki sirkulasi udara yang baik."
    },
    'Pests': {
        'symptoms': "Daun menguning atau terbakar;Muncul bercak cokelat pada daun;Daun menggulung atau berkerut",
        'cause': "Penggunaan pestisida yang berlebihan;Jenis pestisida tidak sesuai dengan tanaman;Pencampuran pestisida yang tidak sesuai",
        'treatment': "Menggunakan pestisida dengan dosis yang tepat dan sesuai.;Hindari kontak langsung dengan bagian tanaman yang sensitive seperti pucuk daun.;Potong bagian tanaman yang rusak untuk mencegah penyebaran lebih lanjut."
    },
    'Virus': {
        'symptoms': "Bintik-bintik atau pita kuning di sepanjang urat daun.;Daun rontok;Muncul bercak atau cincin berwarna kuning, coklat atau putih pada daun.",
        'cause': "Disebarkan oleh serangga;Hama kutu daun;Alat yang digunakan terkontaminasi virus",
        'treatment': "Pangkas bagian yang terinfeksi.;Hindari menyentuh tanaman (selalu mencuci tangan sebelum dan sesudah merawat tanaman);Menggunakan insektisida yang tepat untuk membasmi serangga;Sterilisasi alat yang digunakan dalam merawat tanaman."
    },
    'Healthy' : {
        'symptoms': "Tanaman sehat",
        'cause': 'Tanaman sehat',
        'treatment': "Siram tanaman secara teratur, tetapi jangan berlebihan.;Pastikan tanaman mendapatkan cahaya yang cukup setiap hari.; Bersihkan daun secara rutin dari debu dan kotoran.;Pindahkan ke pot yang lebih besar jika diperlukan untuk pertumbuhan."
    }
}

@router.post("/predict")
async def predict_image(db: db_dependency, userId: int = Form(...),plantId: int = Form(...) ,image: UploadFile = File(...), request: Request):
    if image.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Invalid image file")
    try:
        # Generate a new filename
        new_filename = generate_new_filename(image, userId)

        # Save file locally
        image_path = save_file_locally(image, new_filename)

        # Load the image from the saved file
        image = Image.open(image_path)
        
        # Preprocess the image
        processed_image = preprocess_image(image, target_size=(128, 128))
        
        # Predict the image
        prediction = model.predict(processed_image)
        predicted_class_index = np.argmax(prediction, axis=1)[0]

        # Map the predicted index to the actual label using the label encoder
        predicted_class_label = label_encoder.inverse_transform([predicted_class_index])[0]
        
        # Get the corresponding row from the dataset
        info = data_info.get(predicted_class_label, {})
        category = predicted_class_label
        symptoms = info.get('symptoms', 'No symptoms available')
        cause = info.get('cause', 'No cause information available')
        treatment = info.get('treatment', 'No treatment information available')
        confidence_score = float(prediction[0][predicted_class_index])  # Convert numpy.float32 to float

        # Create full URL for the image
        base_url = str(request.base_url)  # Get the base URL from the request
        full_image_url = f"{base_url}{image_path}"  # Combine base URL with image path

        # Save the results to the database
        new_detection = Detection(
            user_id=userId,
            plant_id=plantId,
            category=category,
            symptoms=symptoms,
            cause=cause,
            treatment=treatment,
            confidence_score=confidence_score,
            image_url=full_image_url
        )
        db.add(new_detection)
        db.commit()
        db.refresh(new_detection)

        return {
            "status": 200,
            "msg": "Success Upload and Detect",
            "data": {
                "detection": new_detection,
                "image_url": full_image_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def get_detections(db: db_dependency):
    with db.connection() as conn:
        query = sqlalchemy.text(
            'SELECT * FROM public.user_detection'
        )
        detections = pd.read_sql(query, conn)
    return {
        "status": 200,
        "msg": "Success Get Detections",
        "data": detections.to_dict('records')
    }

@router.get("/detail")
async def get_detection_detail(detectionId: int, db: db_dependency):
    with db.connection() as conn:
        query = sqlalchemy.text(
            'SELECT * FROM public.user_detection WHERE id = :detectionId'
        )
        data = pd.read_sql(query, conn, params={'detectionId': detectionId})

    if data.empty:
        raise HTTPException(status_code=404, detail=f"Detection with detectionId {detectionId} not found")

    return {
        "status": 200,
        "msg": "Success Get Detection Details",
        "data": data.to_dict('records')
    }

@router.get("/userDetections/{userId}")
async def get_user_detections(userId: int, db: db_dependency):
    with db.connection() as conn:
        query = sqlalchemy.text(
            'SELECT * FROM public.user_detection WHERE user_id = :userId'
        )
        data = pd.read_sql(query, conn, params={'userId': userId})

    if data.empty:
        raise HTTPException(status_code=404, detail=f"User with userId {userId} has no detections")

    return {
        "status": 200,
        "msg": "Success Get User Detections",
        "data": data.to_dict('records')
    }

@router.get("/history/{plantId}")
async def get_detection_detail(plantId: int, db: db_dependency):
    with db.connection() as conn:
        query = sqlalchemy.text(
            'SELECT * FROM public.user_detection WHERE plant_id = :plantId'
        )
        data = pd.read_sql(query, conn, params={'plantId': plantId})

    if data.empty:
        raise HTTPException(status_code=404, detail=f"Detection with detectionId {plantId} not found")

    return {
        "status": 200,
        "msg": "Success Get Detection History",
        "data": data.to_dict('records')
    }
