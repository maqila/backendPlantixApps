from fastapi import HTTPException, Depends, APIRouter, Form, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import db_dependency
from model import User, Token
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Annotated
from sqlalchemy import select

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

# Token Configurations
ACCESS_TOKEN_EXPIRE_MINUTES = 45
SECRET_KEY = "cornelialtboro"
ALGORITHM = "HS256"

# Hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
    
# Function to authenticate user
def authenticate_user(email: str, password: str, db):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return False
    return user

# Function to create access token
def create_access_token(email: str, id: int, expires_delta: timedelta):
    encode = {'sub': email, 'id': id}
    expire = datetime.utcnow() + expires_delta
    encode.update({"exp": expire})
    encoded_jwt = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        id: int = payload.get('id')
        if email is None or id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='cloud not validate user.')
        return {'email': email, 'id': id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='cloud not validate user.')

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    # Check if username is already taken
    existing_username = db.execute(select(User).filter(User.username == username))
    if existing_username.scalar():
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email is already taken
    existing_email = db.execute(select(User).filter(User.email == email))
    if existing_email.scalar():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    create_user = User(
        username = username,
        email = email,
        password_hash = pwd_context.hash(password)
    )
    db.add(create_user)
    db.commit()
    return {"message": "User created successfully"}

@router.post("/login", response_model=Token)
async def login_for_acces_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='cloud not validate user.')
    token = create_access_token(user.email, user.id, timedelta(minutes=60))
    return {'userId': user.id, 'username': user.username, 'access_token': token, 'token_type': 'Bearer'}