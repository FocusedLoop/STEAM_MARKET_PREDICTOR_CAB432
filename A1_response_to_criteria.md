Assignment 1 - REST API Project - Response to Criteria
================================================

Overview
------------------------------------------------

- **Name:** Joshua Wlodarczyk
- **Student number:** n11275561
- **Application name:** Steam Market Predictor
- **Two line description:** The REST API predicts item prices over time using a Random Forest ML model trained on Steam market history data provided by the user. The web app helps users collect and upload this data, organize items into groups, and visualize predictions as graphs.


Core criteria
------------------------------------------------

### Containerise the app

- **ECR Repository name:** n11275561_assessment_1
- **Video timestamp:** 4:30
- **Relevant files:**
    - docker-compose.dev.yml
    - docker-compose.yml
    - app/Dockerfile
    - app/web/Dockerfile

### Deploy the container

- **EC2 instance ID:** i-0f279508021689552
- **Video timestamp:** 4:30 (aws) and 4:50 (Console)

### User login

- **One line description:** MariaDB database with username, password, userid, steamid. Using JWTs for sessions
- **Video timestamp:** 0:25
- **Relevant files:**
    - app/auth/jwt.py
    - app/db/db.py
    - app/models/models_user.py
    - app/models/controllers_users.py

### REST API

- **One line description:** Rest API with endpoints and HTTP methods (GET, POST, PUT, DELETE), and appropiate status codes
- **Video timestamp:** 0:30
- **Relevant files:**
    - app/routes/routes_items.py
    - app/controllers/controllers_items.py
    - app/controllers/controllers_ml.py
    - app/routes/routes_steam.py
    - app/controllers/controllers_steam.py
    - app/routes/routes_users.py
    - app/controllers/controllers_users.py

### Data types

- **One line description:**
- **Video timestamp:**
- **Relevant files:**
    - 

#### First kind

- **One line description:** Raw steam market price history data in JSON form. Stored in MariaDB as text
- **Type:** UnStructured
- **Rationale:** Need to be able to assign items to groups and users so a Query able database is needed to do this
- **Video timestamp:** 4:05
- **Relevant files:**
    - app/controllers/controllers_ml.py
    - app/models/models_ml.py
    - app/utils/ml_utils.py

#### Second kind

- **One line description:** Model and Scaler joblin files for using the models
- **Type:** Structured
- **Rationale:**
- **Video timestamp:**
- **Relevant files:**
  - 

### CPU intensive task

 **One line description:**
- **Video timestamp:** 
- **Relevant files:**
    - 

### CPU load testing

 **One line description:**
- **Video timestamp:** 
- **Relevant files:**
    - 

Additional criteria
------------------------------------------------

### Extensive REST API features

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### External API(s)

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Additional types of data

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Custom processing

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Infrastructure as code

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Web client

- **One line description:**
- **Video timestamp:**
- **Relevant files:**
    -   

### Upon request

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 