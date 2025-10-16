# NOTE - RUN THIS SCRIPT FROM THE ROOT OF THE REPO

# ECR login
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com

# API
docker build -f api/app/Dockerfile -t steam-predictor-api .
docker tag steam-predictor-api:latest 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-api:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-api:latest

# Redis
docker pull redis:7-alpine
docker tag redis:7-alpine 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-redis:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-redis:latest

# Web
docker build -f api/web/Dockerfile -t steam-predictor-web api/web
docker tag steam-predictor-web:latest 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-web:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-web:latest

# Sklearn worker
docker build -f api/sklearn_worker/Dockerfile -t steam-predictor-sklearn .
docker tag steam-predictor-sklearn:latest 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-sklearn:latest
docker push 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-sklearn:latest

# Update services
for SERVICE in steam-predictor-api steam-predictor-web steam-predictor-redis steam-predictor-sklearn; do
  LATEST_REVISION=$(aws ecs list-task-definitions --family-prefix $SERVICE --sort DESC --max-items 1 --query "taskDefinitionArns[0]" --output text | awk -F: '{print $NF}')
  aws ecs update-service \
    --cluster steam-predictor-cluster \
    --service $SERVICE \
    --task-definition $SERVICE:$LATEST_REVISION \
    --force-new-deployment > /dev/null
done