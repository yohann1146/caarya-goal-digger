from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import jwt

#backend modules
from ai_modules import sendGeminiMsg, readGeminiMsg
from database import *
from utils import *
from models import *

VERSION = "0.0.0"
origins = ["http://localhost:8000"]

app = FastAPI(title="VibeWealth API", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/auth/signup")
def register(user_create: UserCreate):
    if users_collection.find_one({"email": user_create.email}):
        raise HTTPException(status_code=400, detail="Invalid or duplicate email.")
    
    user = User(
        first_name=user_create.name,
        email=user_create.email,
        password=user_create.password)
    
    user_JSON = user.model_dump_json()
    users_collection.insert_one(user_JSON)

    access_token = create_access_token(user.id)
    send_verification(user.email, access_token)

    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.post("/auth/verify-email")
def verify_email(email: EmailStr, token: str):
    user = users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user.get("is_verified"):
        return {"message": "Email is already verified."}

    if user.get("verification_token") != token:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
    
    users_collection.update_one(
        { "email": email },
        {"$set": {"is_verified": True}}
    )

    return {"message": "Email verified."}


@app.post("/auth/login", response_model=dict)
def login(user_email: str, user_password: str):
    user = users_collection.find_one({"email": user_email})
    
    if not user:
        raise HTTPException(status_code=400, detail="Email not registered.")
    
    if user.password != user_password:
        raise HTTPException(status_code=401, detail="Incorrect password.")
    
    access_token = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer", "user": user.name, "message": "Login successful."}
    #returns TOKEN TYPE also.

@app.post("/auth/google")
def login_google(user_email: str, user_name: str):
    user = users_collection.find_one({"email": user_email})

    if user:
        token = create_access_token({"sub": user.id})
        return {
            "access_token": token,
            "token_type": "bearer",
            "isNew": False
        }       #returns TOKEN TYPE also. (bearer)
    
    new_user = User(
        first_name=user_name,
        email=user_email,
        is_verified=True)
    
    new_user_json = new_user.model_dump_json()
    users_collection.insert_one(new_user_json)
    new_token = create_access_token(new_user_json.id)

    return {
            "access_token": new_token,
            "token_type": "bearer",
            "isNew": True
        }

@app.post("/auth/forgot-password")
def request_password_reset(email: str):
    user = users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="Email not found.")
    
    send_reset_password(email)
    return {"message": "Password reset email sent."}

@app.post("/auth/reset-password")
def reset_password(email: str, new_password: str):
    user = users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="Email not found.")

    users_collection.update_one(
        { "email": email},
        {"$set": {"password": new_password}}
    )

    return {"message": "Password reset successfully."}

@app.post("/subscribe")
def subscribe_email(user_email: str):
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or duplicate email.")
    
    new_sub = Subscription(
        id= user.id,
        email= user_email)
    
    new_sub_json = new_sub.model_dump_json
    subscriptions_collection.insert_one(new_sub_json)

    return {"message": "Subscription successful."}
