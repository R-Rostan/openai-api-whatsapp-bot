ROLE_NAME="wppMessages-lambda-role"
LAMBDA_NAME="wppMessages"

echo "Creating trust policy..."
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file://role_trust_policy.json
echo "Success!"

echo "Attaching AWSLambdaBasicExecutionRole policy..."
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
echo "Success!"

echo "Adding permission policies to the ${ROLE_NAME} Lambda function..."
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name S3DynamoPermission \
  --policy-document file://role_permission_policy.json
echo "Success!"

echo "Waiting role propagation..."
sleep 15

echo "Creating ${ROLE_NAME} Lambda function..."
aws lambda create-function \
    --function-name $LAMBDA_NAME \
    --package-type Image \
    --code ImageUri="${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/wpp-messages:latest" \
    --role $(aws iam get-role --role-name "$ROLE_NAME" --query "Role.Arn" --output text) \
    --region "$AWS_REGION" \
    --timeout 15 \
    --memory-size 128
echo "Success!"