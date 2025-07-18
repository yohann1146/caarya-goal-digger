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
    user = users_collection.find_one({"email": user_email})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or duplicate email.")
    
    new_sub = Subscription(
        id= user.id,
        email= user_email)
    
    new_sub_json = new_sub.model_dump_json
    subscriptions_collection.insert_one(new_sub_json)

    return {"message": "Subscription successful."}



@app.get("/stocks/top")
def get_top_stocks():
    return get_top_movers()


'''GOAL ENDPOINTS'''
@app.get("/goals/summary")
def get_goals_list(user_id: int):
    goals = goals_collection.find({'user_id': user_id}).sort('target_date')
    if not goals:
        return {"message": "User has not stored any goals."}
    
    return goals

@app.post("/goals/{goal_name}")
def add_goal(goal_name: str, user_id: int,
             targ_amt: int, curr_amt: int,
             targ_date: datetime, gtype: GoalType):
    goal = Goal(
        name=goal_name,
        user_id=user_id,
        target_amount=targ_amt,
        current_amount=curr_amt,
        target_date=targ_date,
        goal_type=GoalType
    )

    goal_json = goal.model_dump_json()
    goals_collection.insert_one(goal_json)

    return {"amount": goal.target_amount,
            "name": goal.name,
            "created_at":datetime.now()}


'''USER SETTINGS ENDPOINTS'''
@app.put("/user/{user_id}/preferences")
def edit_user_preferences(user_id: int, prefs: UserPreferences):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    prefs_json = prefs.model_dump_json()
    users_collection.update_one(
        { "id": user_id},
        {"$set": {"preferences": prefs_json}}
    )

    return prefs_json

@app.post("/user/{user_id}/preferences")
def add_user_preferences(user_id: int, prefs: UserPreferences):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    prefs_json = prefs.model_dump_json()
    users_collection.update_one(
        { "id": user_id},
        {"$set": {"preferences": prefs_json}}
    )

    return prefs_json

@app.post("/user/{user_id}/profile")
def add_user_info(user_id: int, dob: datetime, last_name: str):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user.preferences.dob = dob
    user.last_name = last_name
    user_json = user.model_dump_json()
    users_collection.insert_one(user_json)

    return user_json

@app.put("/user/{user_id}/password")
def edit_user_password(user_id: int, old_password: str, new_password: str):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user.password != old_password:
        raise HTTPException(status_code=401, detail="Incorrect password.")
    
    users_collection.update_one(
        { "id": user_id},
        {"$set": {"password": new_password}}
    )

    return {"message": "Password changed successfully."}

@app.put("/user/{user_id}/email")
def edit_user_password(user_id: int, new_email: EmailStr):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    users_collection.update_one(
        { "id": user_id},
        {"$set": {"email": new_email}}
    )

    return {"message": "Email changed successfully."}

@app.post("/user/{user_id}/reset-preferences")
def reset_user_preferences(user_id: int):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    defaultPrefs = UserPreferences().model_dump_json()
    users_collection.update_one(
        { "id": user_id},
        {"$set": {"preferences": defaultPrefs}}
    )
    return {"message": "Reset all preferences successfully."}

@app.delete("/user/{user_id}/delete")
def delete_user(user_id: int):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    users_collection.delete_one({"id": user_id})

    return {"message": "Deleted user records successfully."}


'''TRANSACTION ENDPOINTS'''
@app.post("/transactions")
def create_transaction(user_id: int, acc_id: int, amount: int, 
                       trtype: TransactionType, trname: str,
                       trnotes: Optional[str] = Query(default=None, max_length=50)):

   acc = accounts_collection.find_one({"acc_id": acc_id})
   if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")
   
   transaction = Transaction(
       name=trname,
       acc_id=acc_id,
       user_id=user_id,
       amount=amount,
       trans_type=trtype,
       notes=trnotes,
       created_at=datetime.now() 
   )
   transaction_json = transaction.model_dump_json()
   transactions_collection.insert_one(transaction_json)

   if transaction.trans_type.value == "debit":
       newbal = acc.bal - transaction.amount

   else: newbal = acc.bal + transaction.amount

   accounts_collection.update_one(
           {"acc_id": acc_id},
           {"$set": {"bal": newbal}})
   
   return transaction_json

@app.get("/transactions")
def get_transactions(user_id: int, start: Optional[datetime] = None, end: Optional[datetime]=None):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    fltr = {"user_id": user_id}
    if start or end:
        date_fltr={}
        if start: date_fltr["$gte"] = start
        if end: date_fltr["$lte"] = end
        fltr["created_at"] = date_fltr

    trans = transactions_collection.find(fltr)
    trans = list(trans)

    return trans

'''ACCOUNT ENDPOINTS'''
@app.post("/accounts")
def create_account(new_acc: NewAccount, user_id: int):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    account = Account(
        acc_id = new_acc.acc_id,
        user_id = user_id,
        name = new_acc.name,
        bal = 0,
        created_at = datetime.now
    )
    account_json = account.model_dump_json()
    accounts_collection.insert_one(account_json)
    return account_json

@app.get("/accounts/")
def get_account(user_id: int):
    user = users_collection.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    accounts = accounts_collection.find({"user_id": user_id})
    accounts = list(accounts)
    accounts = [a.model_dump_json() for a in accounts]
    
    return accounts

@app.put("/accounts/{account_id}")
def edit_account(account_id: int, user_id: int, bal: int):
    acc = accounts_collection.find_one({"acc_id": account_id})
    
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")
    
    if acc.user_id != user_id:
        return {"message": "Access denied. Account does not belong to user."}

    accounts_collection.update_one(
        { "user_id": user_id},
        {"$set": {"bal": bal}}
    )
    
    return {"message": "Balance edited successfully."}
    

@app.delete("/accounts/{account_id}")
def delete_account(account_id: str, user_id: int):
    acc = accounts_collection.find_one({"acc_id": account_id})
    
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")
    
    if acc.user_id != user_id:
        return {"message": "Access denied. Account does not belong to user."}

    accounts_collection.delete_one({"acc_id": account_id})
    
    return {"message": "Account deleted successfully."}

