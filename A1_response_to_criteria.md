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
- **Partner number:** n11803444
- **Application name:** Steam Market Predictor
- **Two line description:** The REST API predicts item prices over time using a Random Forest ML model trained on Steam market history data provided by the user. The web app helps users collect and upload this data, organize items into groups, and visualize predictions as graphs. This was all hosted on a Micro t3 instance
- **EC2 instance name or ID:** i-044e1085de13ea78f

------------------------------------------------

### Core - First data persistence service

- **AWS service name:** AWS RDS
- **What data is being stored?:** The entire database is a PostgreSQL instance including user, items, groups, models for hash values indexing them to files in the S3 bucket
- **Why is this service suited to this data?:** RDS provides a managed relational database with ACID transactions, complex queries (e.g., joining users, groups, and items), and data integrity for structured, interdependent data like user-owned groups and item price histories. It supports SQL for efficient retrieval and updates, which is essential for the app's group/item management and authentication features.
- **Why are the other services used not suitable for this data?:** S3 is designed for unstructured object storage (files/blobs), not relational queries or transactions. DynamoDB (NoSQL) could handle key-value lookups but lacks the relational schema and SQL support needed for complex relationships (e.g., user-group-item hierarchies) and joins.
- **Bucket/instance/table name:** RDS PostgreSQL instance with schema s439 containing tables: "model_index", "group_items", "groups", "users"
- **Video timestamp:**
- **Relevant files:**
    - app/db/db.py
    - app/models/*
    
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

- **AWS service name:**  [eg. RDS]
- **What data is being stored?:** [eg video metadata]
- **Why is this service suited to this data?:** [eg. ]
- **Why is are the other services used not suitable for this data?:** [eg. Advanced video search requires complex querries which are not available on S3 and inefficient on DynamoDB]
- **Bucket/instance/table name:**
- **Video timestamp:**
- **Relevant files:**
    -

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

- **What data is stored within your application that is not stored in cloud data services?:** Temporary intermediate files such as the ML training queue status (stored in queue_status.txt) and local model artifacts/scalers/features if LOCAL_STORAGE=True (though this is set to False in production, defaulting to S3). The Redis queue itself is containerized and considered cloud-based, but the status file is a local summary for debugging.
- **Why is this data not considered persistent state?:** This data is ephemeral and can be recreated from source (e.g., the queue status can be regenerated from Redis data, and local files are backups or intermediates that are not critical for app operation). If lost, the app continues functioning using cloud-stored data.
- **How does your application ensure data consistency if the app suddenly stops?:** All critical persistent data (user profiles, groups, items, models, and files) is stored in cloud services (RDS, S3, Redis). The app does not rely on local state; upon restart, it reloads from cloud services, ensuring consistency. Temporary local files are not used for core operations and are regenerated as needed.
- **Relevant files:**
    - app/utils/ml_utils.py
    - app/utils/utils_redis.py
    - app/controllers/controllers_items.py
    - app/controllers/controllers_ml.py
    - app/models/models_items.py
    - app/models/models_ml.py
    - app/db/db.py
    - app/tmp/queue_status.txt

### Graceful handling of persistent connections

- **Type of persistent connection and use:** [eg. server-side-events for progress reporting]
- **Method for handling lost connections:** [eg. client responds to lost connection by reconnecting and indicating loss of connection to user until connection is re-established ]
- **Relevant files:**
    -


### Core - Authentication with Cognito

- **User pool name:** a2-pairs-5
- **How are authentication tokens handled by the client?:** The client-side app initiates the login process. Upon successful authentication, the backend API returns a JWT to the client. The client then stores this token in its session state. For all subsequent requests to protected API endpoints, the client includes the JWT in the Authorization header as a Bearer token.
- **Video timestamp:**
- **Relevant files:**
    - api/app/auth/cognito_jwt.py

### Cognito multi-factor authentication

- **What factors are used for authentication:** password and email
- **Video timestamp:**
- **Relevant files:**
    - api/app/controllers/controller_auth.py

### Cognito federated identities

- **Identity providers used:** google
- **Video timestamp:**
- **Relevant files:**
    - web_page.py

### Cognito groups

- **How are groups used to set permissions?:** [eg. 'admin' users can delete and ban other users]
- **Video timestamp:**
- **Relevant files:**
    -

### Core - DNS with Route53

- **Subdomain**: steam-market-price-predictor.cab432.com
- **Video timestamp:**

### Parameter store

- **Parameter names:** /steam-market-predictor/s3-bucket-name, /steam-market-predictor/steam-api-base and /steam-market-predictor/steam-com-base, /steam-market-predictor/cognito-domain, /steam-market-predictor/aws-secret-manager
- **Video timestamp:**
- **Relevant files:**
    - app/aws_values.py

### Secrets manager

- **Secrets names:** n11275561-demosecret
- **Video timestamp:** 
- **Relevant files:**
    - app/aws_values.py

### Infrastructure as code

- **Technology used:** terraform
- **Services deployed:**
    - AWS Cognito
    - AWS S3 (Storage Bucket)
    - AWS Secrets Manager
    - AWS Route 53 
- **Video timestamp:**
- **Relevant files:**
    - infra/provider.tf
    - infra/variables.tf
    - infra/cognito.tf
    - infra/s3.tf
    - infra/secrets.tf
    - infra/network.tf
    - infra/outputs.tf

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
