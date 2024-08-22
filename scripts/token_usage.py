from pymongo import MongoClient
from datetime import datetime
from pprint import pprint
import pandas as pd

# Connect to the MongoDB client
client = MongoClient("mongodb://localhost:27017/")  # Adjust the connection string as needed

# Select the database and collection
db = client["doc_analyse_lite"]
collection = db["your_collection_name"]  # Replace with your collection name

# Define the aggregation pipeline
pipeline = [
    {
        "$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$created_at"}}},
            "total_prompt_tokens": {"$sum": {"$cond": [{"$eq": ["$token", "prompt_tokens"]}, "$count", 0]}},
            "total_completion_tokens": {"$sum": {"$cond": [{"$eq": ["$token", "completion_tokens"]}, "$count", 0]}},
            "total_total_tokens": {"$sum": {"$cond": [{"$eq": ["$token", "total_tokens"]}, "$count", 0]}},
        }
    },
    {
        "$sort": {"_id": 1}  # Sort by date
    }
]

# Execute the aggregation
results = list(collection.aggregate(pipeline))

# Convert to a Pandas DataFrame for tabular display
df = pd.DataFrame(results)

# Rename columns for better readability
df = df.rename(columns={
    "_id": "Date",
    "total_prompt_tokens": "Prompt Tokens",
    "total_completion_tokens": "Completion Tokens",
    "total_total_tokens": "Total Tokens"
})

# Add a Total column
df["Total"] = df["Prompt Tokens"] + df["Completion Tokens"] + df["Total Tokens"]

# Print the DataFrame
print(df)

# If you want to display it in a table format, you can use pprint as well
pprint(df.to_dict('records'))
