import os
from pymongo import MongoClient
from dotenv import load_dotenv

URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")    

client = MongoClient(URI)
db = client[DB_NAME]

users_collection = db["users"]
subscriptions_collection = db["subscriptions"]
accounts_collection = db["accounts"]
transactions_collection = db["transactions"]
goals_collection = db["goals"]