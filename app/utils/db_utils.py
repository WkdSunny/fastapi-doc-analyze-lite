from app.config import database

def insert_document(collection_name, data):
    """Insert a document into a specified collection."""
    collection = database[collection_name]
    return collection.insert_one(data).inserted_id

def find_document(collection_name, query):
    """Find a single document in a specified collection."""
    collection = database[collection_name]
    return collection.find_one(query)

def update_document(collection_name, query, update_data):
    """Update a document in a specified collection."""
    collection = database[collection_name]
    return collection.update_one(query, {'$set': update_data})

def insert_many_documents(collection_name, data_list):
    """Insert multiple documents into a specified collection."""
    collection = database[collection_name]
    return collection.insert_many(data_list).inserted_ids

def find_many_documents(collection_name, query):
    """Find multiple documents in a specified collection."""
    collection = database[collection_name]
    return collection.find(query)
