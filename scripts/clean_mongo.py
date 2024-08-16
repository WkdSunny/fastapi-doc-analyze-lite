from pymongo import MongoClient

def clear_collections(db_name, collections):
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')  # Adjust the connection string if needed
    db = client[db_name]

    # Iterate through the list of collections and clear them
    for collection_name in collections:
        collection = db[collection_name]
        result = collection.delete_many({})
        print(f"Cleared {result.deleted_count} documents from collection '{collection_name}'.")

    # Close the connection
    client.close()

if __name__ == "__main__":
    # Specify the database name
    database_name = "doc_analyse"  # Replace with your database name

    # Specify the collections you want to clear
    collections_to_clear = [
        "Tasks", 
        "Documents", 
        "Segments", 
        "Entities", 
        "DocumentClassification", 
        "Topics", 
        "TFIDFKeywords", 
        "Questions", 
        "Answers", 
        "Labels"
    ]  # Add or remove collection names as needed

    # Clear the specified collections
    clear_collections(database_name, collections_to_clear)

# Run from terminal
# python scripts/clean_mongo.py