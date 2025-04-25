ROLE_NAME="wppMessages-lambda-role"
LAMBDA_NAME="wppMessages"

echo "Deleting permission policies..."
for policy_name in \
    $(aws iam list-role-policies \
        --role-name "$ROLE_NAME" \
        --query 'PolicyNames[]' \
        --output text); do
  echo "Deleting: ${policy_name}..."
  aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "$policy_name"
done
echo "[1/4] Success!"

echo "Detaching trust policies..."
for policy_arn in \
    $(aws iam list-attached-role-policies \
        --role-name "$ROLE_NAME" \
        --query "AttachedPolicies[].PolicyArn" \
        --output text); do
    echo "Detaching: ${policy_arn}..."
    aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn "$policy_arn"
done
echo "[2/4] Success!"

echo "Deleting role ${ROLE_NAME}..."
aws iam delete-role --role-name wppMessages-lambda-role
echo "[3/4] Success!"

echo "Deletin ${LAMBDA_NAME} Lambda function..."
aws lambda delete-function --function-name "$LAMBDA_NAME"
echo "[4/4] Success!"