from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGO_URI)

def get_database():
  return client[settings.MONGO_DB_NAME]