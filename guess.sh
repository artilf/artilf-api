#!/usr/bin/env bash

environment=""
is_assume=false

while getopts ':e:a' args; do
  case "$args" in
    e)
      environment="$OPTARG"
      ;;
    a)
      is_assume=true
      ;;
    *)
      echo "not set environ"
      exit 1
      ;;
  esac
done


if [[ "$environment" == "development" ]]; then
  aws_env="development"
  aws_account_id="$AWS_ACCOUNT_ID_DEVELOPMENT"
  aws_iam_role_arn="$AWS_IAM_ROLE_ARN_DEVELOPMENT"
  aws_iam_role_external_id="$AWS_IAM_ROLE_EXTERNAL_ID_DEVELOPMENT"
  aws_cfn_deploy_role_arn="$AWS_CFN_DEPLOY_ROLE_ARN_DEVELOPMENT"
elif [[ "$environment" == "production" ]]; then
  aws_env="production"
  aws_account_id="$AWS_ACCOUNT_ID_PRODUCTION"
  aws_iam_role_arn="$AWS_IAM_ROLE_ARN_PRODUCTION"
  aws_iam_role_external_id="$AWS_IAM_ROLE_EXTERNAL_ID_PRODUCTION"
  aws_cfn_deploy_role_arn="$AWS_CFN_DEPLOY_ROLE_ARN_PRODUCTION"
else
  exit 1
fi

cat <<EOT
export AWS_ACCOUNT_ID="${aws_account_id}"
export AWS_ENV="${aws_env}"
export AWS_IAM_ROLE_ARN="${aws_iam_role_arn}"
export AWS_IAM_ROLE_EXTERNAL_ID="${aws_iam_role_external_id}"
export AWS_CFN_DEPLOY_ROLE_ARN="${aws_cfn_deploy_role_arn}"
EOT


if [[ ${is_assume} == true ]]; then
  exit 0
fi

aws_sts_credentials="$( \
  aws sts assume-role \
    --role-arn "$aws_iam_role_arn" \
    --role-session-name "$CIRCLE_USERNAME" \
    --external-id "$aws_iam_role_external_id" \
    --duration-seconds "900" \
    --query "Credentials" \
    --output "json"
)"

cat <<EOT
export AWS_ACCESS_KEY_ID="$(echo ${aws_sts_credentials} | jq -r '.AccessKeyId')"
export AWS_SECRET_ACCESS_KEY="$(echo ${aws_sts_credentials} | jq -r '.SecretAccessKey')"
export AWS_SESSION_TOKEN="$(echo ${aws_sts_credentials} | jq -r '.SessionToken')"
EOT
