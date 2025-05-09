ENDPOINT_NAME="wpp"
LAMBDA_GET_METHOD="wpp-webhook-connect"
LAMBDA_POST_METHOD="wpp-messages"

echo "Creating API..."
aws apigateway create-rest-api \
  --name $ENDPOINT_NAME \
  --region $AWS_REGION \
  --endpoint-configuration '{"types":["REGIONAL"]}'

API_ID=$(aws apigateway get-rest-apis --query 'items[?name==`'"${ENDPOINT_NAME}"'`].id | [0]' --output text)
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $AWS_REGION \
    --query 'items[?path==`/`].id | [0]' \
    --output text)

echo "Creating GET method..."
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $ROOT_RESOURCE_ID \
  --http-method GET \
  --authorization-type "NONE"

echo "Creating POST method..."
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $ROOT_RESOURCE_ID \
  --http-method POST \
  --authorization-type "NONE"

echo "Adding lambda integration..."
LAMBDA_FUNCTION_ARN=$(aws lambda list-functions \
    --query 'Functions[?FunctionName==`'"${LAMBDA_GET_METHOD}"'`].FunctionArn | [0]' \
    --output text)
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $ROOT_RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${LAMBDA_FUNCTION_ARN}/invocations

LAMBDA_FUNCTION_ARN=$(aws lambda list-functions \
    --query 'Functions[?FunctionName==`'"${LAMBDA_POST_METHOD}"'`].FunctionArn | [0]' \
    --output text)
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $ROOT_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${LAMBDA_FUNCTION_ARN}/invocations

echo "Deploying API..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name zai

echo "Adding lambda permission..."
aws lambda add-permission \
  --function-name $LAMBDA_GET_METHOD \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*

aws lambda add-permission \
  --function-name $LAMBDA_POST_METHOD \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*