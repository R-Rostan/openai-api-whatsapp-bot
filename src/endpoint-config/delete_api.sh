ENDPOINT_NAME="wpp"
LAMBDA_GET_METHOD="wpp-webhook-connect"
LAMBDA_POST_METHOD="wpp-messages"

API_ID=$(aws apigateway get-rest-apis --query 'items[?name==`'"${ENDPOINT_NAME}"'`].id | [0]' --output text)
aws apigateway delete-rest-api --rest-api-id $API_ID

aws lambda remove-permission \
  --function-name $LAMBDA_GET_METHOD \
  --statement-id apigateway-access

aws lambda remove-permission \
  --function-name $LAMBDA_POST_METHOD \
  --statement-id apigateway-access