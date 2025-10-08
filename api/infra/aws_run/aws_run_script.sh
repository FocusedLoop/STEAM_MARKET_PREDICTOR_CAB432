# ECR login
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com

# API
docker build -t steam-predictor-api ./api
docker tag steam-predictor-api:latest 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-api:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-api:latest

# Redis
docker build -t steam-predictor-redis ./api/redis
docker tag steam-predictor-redis:latest 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-redis:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-redis:latest

# Web
docker build -t steam-predictor-web ./api/web
docker tag steam-predictor-web:latest 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-web:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-web:latest

# Sklearn worker
docker build -t steam-predictor-sklearn ./api/sklearn_worker
docker tag steam-predictor-sklearn:latest 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-sklearn:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-sklearn:latest