Assignment 2 - Cloud Services Exercises - Response to Criteria
================================================

Instructions
------------------------------------------------
- Keep this file named A2_response_to_criteria.md, do not change the name
- Upload this file along with your code in the root directory of your project
- Upload this file in the current Markdown format (.md extension)
- Do not delete or rearrange sections.  If you did not attempt a criterion, leave it blank
- Text inside [ ] like [eg. S3 ] are examples and should be removed


Overview
------------------------------------------------

- **Name:** Joshua Wlodarczyk
- **Student number:** n11275561
- **Partner name:** Zakk Wilson-Christian
- **Partner number:** 
- **Application name:** Steam Market Predictor
- **Two line description:** The REST API predicts item prices over time using a Random Forest ML model trained on Steam market history data provided by the user. The web app helps users collect and upload this data, organize items into groups, and visualize predictions as graphs. This was all hosted on a Micro t3 instance
- **EC2 instance name or ID:** i-044e1085de13ea78f

------------------------------------------------

### Core - First data persistence service

- **AWS service name:**  AWS RDS
- **What data is being stored?:** The entire database is a DynamoDB instance including user, items, groups, models for hash values indexing them to files in the s3 bucket
- **Why is this service suited to this data?:** RDS provides a managed relational database with ACID transactions, complex queries (e.g., joining users, groups, and items), and data integrity for structured, interdependent data like user-owned groups and item price histories. It supports SQL for efficient retrieval and updates, which is essential for the app's group/item management and authentication features.
- **Why is are the other services used not suitable for this data?:** S3 is designed for unstructured object storage (files/blobs), not relational queries or transactions. DynamoDB (NoSQL) could handle key-value lookups but lacks the relational schema and SQL support needed for complex relationships (e.g., user-group-item hierarchies) and joins.
- **Bucket/instance/table name:** Used User and Schema s439 for tables "model_index", "group_items", "groups", "users"
- **Video timestamp:**
- **Relevant files:**
    - app/db/db.py

### Core - Second data persistence service

- **AWS service name:** S3 Object Storage
- **What data is being stored?:** ML model artifacts including trained model files (.joblib), scaler files (.joblib), feature statistics (.json), and training graphs (.png).
- **Why is this service suited to this data?:** S3 is optimized for scalable, durable object storage of large binary files and unstructured data. It supports presigned URLs for secure, direct uploads/downloads without exposing credentials, and it's cost-effective for variable-sized ML artifacts that need global access and versioning.
- **Why is are the other services used not suitable for this data?:** RDS is for structured relational data, not large binary files or blobs. DynamoDB can store small items but isn't ideal for multi-GB model files or direct file streaming; it would require additional logic for uploads/downloads and increase costs for large data. ElastiCache (Redis) is for in-memory caching, not persistent file storage.
- **Bucket/instance/table name:** a2-pairs-5-a2-ml-models-s3-bucket 
- **Video timestamp:**
- **Relevant files:**
    - app/routes/routes_items.py
    - app/controllers_ml.py
    - app/utils/utils_s3.py
    - app/models/models_ml.py

### Third data service

- **AWS service name:** Local Redis Instance (Containerized)
- **What data is being stored?:** Frequently accessed, transient data such as user authentication sessions, group item lists, and intermediate results from model operations. This reduces repeated queries to the relational database and improves application responsiveness.
- **Why is this service suited to this data?:** Redis is an in-memory data store optimized for high-throughput, low-latency access. Running it locally in a container allows for quick setup and testing without external dependencies, while still providing caching for ephemeral data that can be regenerated if lost. It's ideal for development and small-scale production where full ElastiCache isn't needed yet.
- **Why is are the other services used not suitable for this data?:** RDS is designed for durable, structured relational data, but is slower for repeated reads of the same data. S3 is optimized for large, unstructured object storage, not fast retrieval of small, frequently used values. DynamoDB is a persistent NoSQL store, not an in-memory cache, so it doesn’t offer the same millisecond-level performance or eviction policies for temporary data. ElastiCache is cloud-based and more scalable, but a local container is simpler for initial deployment.
- **Bucket/instance/table name:** Local Redis container (e.g., via Docker on the EC2 instance soon to be a seperate instance)
- **Video timestamp:** 
- **Relevant files:**
    - app/utils/utils_redis.py
    - app/controllers/controllers_items.py
    - app/controllers/controllers_ml.py

### S3 Pre-signed URLs

- **S3 Bucket names:** a2-pairs-5-a2-ml-models-s3-bucket 
- **Video timestamp:**
- **Relevant files:**
    - app/utils/utils_s3.py
    - app/controllers/controllers_ml.py

### In-memory cache (WE WHERE APPROVED TO USE REDIS IN A CONTAINER BY UNIT COORDINATOR)

- **ElastiCache instance name:** Local Instance hosted with Redis as a container on the same instance (soon to be another instance for assessment 3)
- **What data is being cached?:** Group items (lists of items belonging to a user-owned group), and other frequently queried relational data like group details to reduce database load.
- **Why is this data likely to be accessed frequently?:** Group items and related data are accessed repeatedly during group management, item addition/removal, and model operations, as users interact with their groups often; caching avoids redundant database queries and improves response times for read-heavy operations.
- **Video timestamp:**
- **Relevant files:**
    - app/utils/utils_redis.py
    - app/controllers/controllers_items.py
    - app/controllers/controllers_ml.py

### Core - Statelessness

- **What data is stored within your application that is not stored in cloud data services?:** [eg. intermediate video files that have been transcoded but not stabilised]
- **Why is this data not considered persistent state?:** [eg. intermediate files can be recreated from source if they are lost]
- **How does your application ensure data consistency if the app suddenly stops?:** [eg. journal used to record data transactions before they are done.  A separate task scans the journal and corrects problems on startup and once every 5 minutes afterwards. ]
- **Relevant files:**
    -

### Graceful handling of persistent connections

- **Type of persistent connection and use:** [eg. server-side-events for progress reporting]
- **Method for handling lost connections:** [eg. client responds to lost connection by reconnecting and indicating loss of connection to user until connection is re-established ]
- **Relevant files:**
    -


### Core - Authentication with Cognito

- **User pool name:**
- **How are authentication tokens handled by the client?:** [eg. Response to login request sets a cookie containing the token.]
- **Video timestamp:**
- **Relevant files:**
    -

### Cognito multi-factor authentication

- **What factors are used for authentication:** [eg. password, SMS code]
- **Video timestamp:**
- **Relevant files:**
    -

### Cognito federated identities

- **Identity providers used:**
- **Video timestamp:**
- **Relevant files:**
    -

### Cognito groups

- **How are groups used to set permissions?:** [eg. 'admin' users can delete and ban other users]
- **Video timestamp:**
- **Relevant files:**
    -

### Core - DNS with Route53

- **Subdomain**:  [eg. myawesomeapp.cab432.com]
- **Video timestamp:**

### Parameter store

- **Parameter names:** /steam-market-predictor/s3-bucket-name, /steam-market-predictor/steam-api-base and /steam-market-predictor/steam-com-base
- **Video timestamp:**
- **Relevant files:**
    - app/aws_values.py

### Secrets manager

- **Secrets names:** [eg. n1234567-youtube-api-key]
- **Video timestamp:**
- **Relevant files:**
    -

### Infrastructure as code

- **Technology used:**
- **Services deployed:**
- **Video timestamp:**
- **Relevant files:**
    -

### Other (with prior approval only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    -

### Other (with prior permission only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    -
