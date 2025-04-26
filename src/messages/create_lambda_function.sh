LAMBDA_NAME="wpp-messages"

echo "Creating trust policy..."
aws iam create-role \
    --role-name ${LAMBDA_NAME}-lambda-role \
    --assume-role-policy-document file://role_trust_policy.json

echo "Attaching AWSLambdaBasicExecutionRole policy..."
aws iam attach-role-policy \
  --role-name ${LAMBDA_NAME}-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

echo "Adding permission policies to the ${LAMBDA_NAME} Lambda function..."
aws iam put-role-policy \
  --role-name ${LAMBDA_NAME}-lambda-role \
  --policy-name S3DynamoPermission \
  --policy-document file://role_permission_policy.json

echo "Waiting role propagation..."
sleep 15

echo "Creating ${LAMBDA_NAME} Docker Image..."
docker buildx build --platform linux/amd64 --provenance=false -t ${LAMBDA_NAME}-image:latest .

echo "Creating ${LAMBDA_NAME} ECR Repository"
aws ecr create-repository --repository-name ${LAMBDA_NAME}-image

echo "Uploading docker image to the ${LAMBDA_NAME} ECR Repository..."
aws ecr get-login-password \
  --region ${AWS_REGION} | docker login \
  --username AWS \
  --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

sleep 5
docker tag ${LAMBDA_NAME}-image:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${LAMBDA_NAME}-image:latest

sleep 5
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${LAMBDA_NAME}-image:latest

sleep 10
echo "Creating ${LAMBDA_NAME} Lambda function..."
aws lambda create-function \
    --function-name $LAMBDA_NAME \
    --package-type Image \
    --code ImageUri="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${LAMBDA_NAME}-image:latest" \
    --role $(aws iam get-role --role-name "${LAMBDA_NAME}-lambda-role" --query "Role.Arn" --output text) \
    --region "$AWS_REGION" \
    --timeout 15 \
    --memory-size 128

sleep 10
aws lambda update-function-configuration \
  --function-name $LAMBDA_NAME \
  --environment "Variables={\
    META_WPP_API_TOKEN=${META_WPP_API_TOKEN},\
    OPENAI_API_KEY=${OPENAI_API_KEY},\
    WHATSAPP_BUSINESS_PHONE_NUMBER_ID=${WHATSAPP_BUSINESS_PHONE_NUMBER_ID}}"