# 🧩 Issue: Qdrant Collection Already Exists Error

## 🧾 Issue

The code attempts to create a Qdrant collection that already exists, causing a conflict error (HTTP 409).

```py
client = QdrantClient(
    url="http://<QDRANT-HOST>:<PORT>/"
)

collection_name = "<COLLECTION-NAME>"

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=<VECTOR-SIZE>,
        distance=Distance.<DISTANCE-METRIC>
    )
)
```

```cmd
qdrant_client.http.exceptions.UnexpectedResponse: Unexpected Response: 409 (Conflict)
Raw response content:
b'{"status":{"error":"Wrong input: Collection `<COLLECTION-NAME>` already exists!"},"time":0.000778774}'
```

## 🛠️ Fix

1. **Check if collection exists before creation.**  
   Prevents conflict by verifying whether the specified collection already exists in Qdrant.

2. **Delete the existing collection if found.**  
   Removes the pre-existing collection so a new one can be created cleanly.

3. **Recreate the collection after cleanup.**  
   Creates a fresh collection without triggering a conflict error.

```py
client = QdrantClient(
    url="http://<QDRANT-HOST>:<PORT>/"
)

collection_name = "<COLLECTION-NAME>"

if client.collection_exists(collection_name=collection_name):
    client.delete_collection(collection_name=collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=<VECTOR-SIZE>,
        distance=Distance.<DISTANCE-METRIC>
    )
)
```

# ⚙️ Issue: Qdrant Client Initialization Conflict

## 🧾 Issue

The code specifies multiple connection parameters (`location`, `host`, `https`, and `port`) together, which leads to a `ValueError` since only one connection method should be defined.

```py
client = QdrantClient(
    location="<STRING-PATH>",
    https=True,
    host="<HOST-NAME>",
    port=<PORT-NUMBER>
)
```

```cmd
   raise ValueError(
ValueError: Only one of <location>, <url>, <host> or <path> should be specified.
```

## 🛠️ Fix

1. **Use a single connection parameter (`url`).**  
   Replace multiple connection arguments with a unified `url` definition to remove ambiguity.
2. **Ensure the correct protocol and endpoint are used.**  
   Specify the complete URL string (`http://<HOST>:<PORT>/`) for a valid Qdrant connection.

```py
client = QdrantClient(
    url="http://<HOST-NAME>:<PORT-NUMBER>/"
)
```
