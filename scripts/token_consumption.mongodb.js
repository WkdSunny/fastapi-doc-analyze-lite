/* global use, db */
// MongoDB Playground
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.

// The current database to use.
use('doc_analyse_lite');

// Search for documents in the current collection.
db.getCollection('TokenUsage')
  .aggregate([
    {
      "$group": {
        "_id": "$token", // Group by the token field
        "totalCount": { "$sum": "$count" } // Sum the count field for each token
      }
    },
    {
      "$project": {
        "_id": 0, // Exclude the _id field from the result
        "token": "$_id", // Include the token field
        "totalCount": 1 // Include the total count
      }
    }
  ])