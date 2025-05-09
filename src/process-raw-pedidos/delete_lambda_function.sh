LAMBDA_NAME="wpp-raw-process"

echo "Deleting permission policies..."
for policy_name in \
    $(aws iam list-role-policies \
        --role-name "${LAMBDA_NAME}-lambda-role" \
        --query 'PolicyNames[]' \
        --output text); do
  echo "Deleting: ${policy_name}..."
  aws iam delete-role-policy --role-name "${LAMBDA_NAME}-lambda-role" --policy-name "$policy_name"
done

echo "Detaching trust policies..."
for policy_arn in \
    $(aws iam list-attached-role-policies \
        --role-name "${LAMBDA_NAME}-lambda-role" \
        --query "AttachedPolicies[].PolicyArn" \
        --output text); do
    echo "Detaching: ${policy_arn}..."
    aws iam detach-role-policy --role-name "${LAMBDA_NAME}-lambda-role" --policy-arn "$policy_arn"
done

echo "Deleting role ${LAMBDA_NAME}-lambda-role..."
aws iam delete-role --role-name ${LAMBDA_NAME}-lambda-role

aws ecr batch-delete-image \
    --repository-name ${LAMBDA_NAME}-image \
    --image-ids imageTag=latest

echo "Deleting ${LAMBDA_NAME} ECR Repository..."
aws ecr delete-repository --repository-name ${LAMBDA_NAME}-image

echo "Deleting ${LAMBDA_NAME} Lambda function..."
aws lambda delete-function --function-name "$LAMBDA_NAME"