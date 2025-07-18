# models.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date, timedelta
from typing import Optional
import uuid

from pydantic import BaseModel
from typing import Annotated
from datetime import datetime
from enum import Enum

#ENUMS
class DateRange(Enum, str):
    CURR = "current",
    WEEKLY = "this_week",
    MONTHLY ="this_month",
    MONTHS_6 = "last_6_months",
    YEARLY = "this_year"
    CUSTOM = "custom"

class TransactionType(Enum, str):
    TO = "credit",
    FROM = "debit"
    TRANSFER = "transfer"

class GoalType(Enum, str):
    EDU = "educational"
    JOB = "occupational"
    PERSONAL = "personal"
    HOUSE = "housing"
    INSURANCE = "insurance"

class ColorMode(Enum, str):
    DARK = "dark"
    LIGHT = "light"


#MODELS
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str  #hashing? will do later idk

class UserPreferences(BaseModel):
    country: Optional[str] = None
    color_mode: Optional[ColorMode] = "light"
    currency: Optional[str] = "usd"
    date_format: Optional[str] = "DD-MM-YYYY"
    language: Optional[str] = "en"

class User(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    dob: datetime
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_verified: bool = False
    email: EmailStr
    password: str           #new fields i added

    preferences: UserPreferences

class Subscription(BaseModel):
    id: str
    email: EmailStr
    subscribed_at: datetime = Field(default_factory=datetime.now())

class NewAccount(BaseModel):
    acc_id: int
    name: str

class Account(BaseModel):
    acc_id: int = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    name: str
    bal: int
    created_at: datetime

class Transaction(BaseModel):
    name: str
    trans_id: int = Field(default_factory=lambda: str(uuid.uuid4()))
    acc_id: int
    amount: int
    trans_type: TransactionType
    created_at: datetime
    notes: Optional[str] = None

class Goal(BaseModel):
    name: str
    user_id: int
    goal_id: id = Field(default_factory=lambda: str(uuid.uuid4()))
    target_amount: int
    current_amount: int = 0
    target_date: datetime = Field(default_factory=datetime.now()+timedelta(days=365)) #by default, goal is set a year from now
    color: str = "#FFFFFF"
    goal_type: GoalType