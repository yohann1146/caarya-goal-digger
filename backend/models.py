# models.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel
from typing import Annotated
from datetime import datetime
from enum import Enum

#ENUMS
class TransactionType(Enum, str):
    TO = "credit",
    FROM = "debit"

class GoalType(Enum, str):
    EDU = "educational"
    JOB = "occupational"
    PERSONAL = "personal"
    HOUSE = "housing"
    INSURANCE = "insurance"

class GoalLength(Enum, str):
    LONG = "long-term"
    INTERMEDIATE = "intermediate"
    SHORT = "short-term"

class ColorMode(Enum, str):
    DARK = "dark"
    LIGHT = "light"


#MODELS
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str  #hashing? will do later idk

class User(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_verified: bool = False
    email: EmailStr
    password: str           #new fields i added

    dob: datetime
    country: Optional[str] = None
    color_mode: ColorMode
    currency: str
    date_format: str
    language: str

class Subscription(BaseModel):
    id: str
    email: EmailStr
    subscribed_at: datetime = Field(default_factory=datetime.now())

class NewAccount(BaseModel):
    acc_id: int
    name: str

class Account(BaseModel):
    acc_id: int
    user_id: int
    name: str
    bal: int
    created_at: datetime

class Transaction(BaseModel):
    trans_id: int
    acc_id: int
    amount: int
    trans_type: TransactionType
    created_at: datetime

class Goal(BaseModel):
    goal_id: int
    name: str
    desc: str | None
    user_id: int