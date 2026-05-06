from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext

app = FastAPI()

# 🔐 Secret key (later move to env)
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fake DB (for now)
users_db = {}


# 📦 Models
class User(BaseModel):
    username: str
    password: str


# 🔹 Register
@app.post("/users/register")
def register(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)

    users_db[user.username] = {
        "username": user.username,
        "password": hashed_password
    }

    return {"message": "User registered"}


# 🔹 Login
@app.post("/users/login")
def login(user: User):
    db_user = users_db.get(user.username)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = jwt.encode(
        {"sub": user.username},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {"access_token": token}