Assignment 1 - REST API Project - Response to Criteria
================================================

Overview
------------------------------------------------

- **Name:** Joshua Wlodarczyk
- **Student number:** n11275561
- **Application name:** Steam Market Predictor
- **Two line description:** The REST API predicts item prices over time using a Random Forest ML model trained on Steam market history data provided by the user. The web app helps users collect and upload this data, organize items into groups, and visualize predictions as graphs. This was all hosted on a Micro t3 instance


Core criteria
------------------------------------------------

### Containerise the app

- **ECR Repository name:** n11275561_assessment_1
- **Video timestamp:** 4:30 (aws) and 4:45 (Console)
- **Relevant files:**
    - docker-compose.dev.yml
    - docker-compose.yml
    - app/Dockerfile
    - app/web/Dockerfile

### Deploy the container

- **EC2 instance ID:** i-0f279508021689552
- **Video timestamp:** 4:30 (aws) and 4:45 (Console)

### User login

- **One line description:** MariaDB database with username, password, userid, steamid. Using JWTs for sessions
- **Video timestamp:** 0:25
- **Relevant files:**
    - app/auth/jwt.py
    - app/db/db.py
    - app/models/models_users.py
    - app/controllers/controllers_users.py
    - .env.example

### REST API

- **One line description:** Rest API with endpoints and HTTP methods (GET, POST, PUT, DELETE), and appropiate status codes
- **Video timestamp:** 3:25 (full breakdown), 0:40
- **Relevant files:**
    - app/routes/routes_items.py
    - app/controllers/controllers_items.py
    - app/controllers/controllers_ml.py
    - app/routes/routes_steam.py
    - app/controllers/controllers_steam.py
    - app/routes/routes_users.py
    - app/controllers/controllers_users.py

### Data types

- **One line description:** Application makes use of both structured relational data (model index database in MariaDB) and unstructured binary artifacts (joblib model and scaler files).  
- **Video timestamp:** 1:52, 2:15, 0:23
- **Relevant files:**  
  - app/controllers/controllers_ml.py  
  - app/models/models_ml.py  
  - app/utils/ml_utils.py  
  - tmp/  

#### First kind

- **One line description:** Model index database linking generated models to groups and items (stores id, user ownership, hash, model paths, flags, etc.)
- **Type:** Structured
- **Rationale:** Data is stored in MariaDB tables with a defined schema (ids, ownership, file paths, flags). This allows efficient queries to tie models back to users and groups.
- **Video timestamp:** 2:58
- **Relevant files:**
  - app/controllers/controllers_ml.py
  - app/models/models_ml.py
  - app/utils/ml_utils.py

#### Second kind

- **One line description:** Model and Scaler joblib files generated during training
- **Type:** UnStructured
- **Rationale:** These are binary artifacts without a queryable schema. They cannot be stored or queried directly in MariaDB, only referenced by path from the model index.
- **Video timestamp:** 4:05
- **Relevant files:**
  - app/utils/ml_utils.py
  - app/controllers/controllers_ml.py
  - tmp/.

### CPU intensive task

- **One line description:** Implementation of a shared job queue in `PriceModel` to handle machine learning tasks efficiently across multiple users.  
- **Video timestamp:**  3:54
- **Relevant files:** 
  - app/utils/ml_utils.py  
  - app/controllers/controllers_ml.py  
  - tmp/queue_status.txt

### CPU load testing

- **One line description:** Stress testing the shared job queue to maintain steady CPU usage by keeping the queue full and monitoring performance.  
- **Video timestamp:** 4:50
- **Relevant files:**  
  - app/utils/ml_utils.py  
  - tmp/queue_status.txt  

Additional criteria
------------------------------------------------

### Extensive REST API features

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### External API(s)

- **One line description:** Integrates the Steam Web API (IPlayerService, ISteamEconomy) and Steam Community endpoints as primary data sources to fetch owned games, user inventory, resolve `market_hash_name`, and generate price-history URLs for steam by the API.
- **Video timestamp:** 1:37, 3:31
- **Relevant files:**
  - app/services/steam.py
  - app/controllers/controllers_steam.py
  - app/routes/routes_steam.py
  - .env.example
  - web/web_page.py

### Additional types of data

- **One line description:** Application uses three distinct types of data: structured relational tables, unstructured model/data files, and hard saved json data in the tmp dir
- **Video timestamp:** 3:55
- **Relevant files:**   
  - app/utils/ml_utils.py
  - app/tmp/.


### Custom processing

- **One line description:** Application implements a custom ML pipeline with domain-specific feature engineering, a managed job queue for multi-user training, and tailored persistence/visualisation of Steam market predictions.
- **Video timestamp:** 3:55
- **Relevant files:**  
  - app/utils/ml_utils.py  
  - app/controllers/controllers_ml.py
  - tmp/models/
  - tmp/scalers/
  - tmp/features/

### Infrastructure as code

- **One line description:** Application deployment is automated using Docker Compose files that define and launch all required services (API server, web frontend, and MariaDB database) from a single command.  
- **Video timestamp:** 2:22, 4:44
- **Relevant files:**  
  - docker-compose.yml  
  - docker-compose.dev.yml  
  - Dockerfile  
  - web/Dockerfile  

### Web client

- **One line description:** A full-featured Streamlit web client provides a browser-accessible interface to all API endpoints, including authentication, group and item management, Steam integration, and ML training/prediction with visual outputs.  
- **Video timestamp:** 0:10 
- **Relevant files:**  
  - web/web_page.py

### Upon request

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 