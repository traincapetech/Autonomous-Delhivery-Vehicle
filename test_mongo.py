from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

db = client['my_database']
collection = db['my_collection']

print(f"Database: {db.name}")
print(f"Collection: {collection.name}")

sample_document = {"name": "Alice", "age": 30, "city": "New York"}
collection.insert_one(sample_document)

document = collection.find_one({"name": "Alice"})
print("Inserted Document:", document)
