import pymongo
from pymongo.errors import ServerSelectionTimeoutError

try:
    client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.server_info()  # Forces a connection call
    print("Connected to MongoDB!")
except ServerSelectionTimeoutError as e:
    print("Could not connect to MongoDB:", e)
