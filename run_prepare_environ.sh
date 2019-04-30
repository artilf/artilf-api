#!/usr/bin/env bash

set -xeu

environment=""
get_flag=false
template_path="src/00_prepare_environ.yml"

while getopts ':e:g' args; do
  case "$args" in
    e)
      environment="$OPTARG"
      ;;
     g)
      get_flag=true
      ;;
  esac
done

echo ${environment} | grep -qE '^(development|production)$' || { echo "Invalid environment name: $environment"; exit 1; }

export AWS_PROFILE=bibl-${environment}

stack_name="bibl-prepare-environ-${environment}"

if [[ "$get_flag" == false ]]; then
  pipenv run cfn-lint --template ${template_path}

  pipenv run aws cloudformation deploy \
    --no-execute-changeset \
    --template-file ${template_path} \
    --stack-name ${stack_name} \
    --capabilities "CAPABILITY_IAM" "CAPABILITY_NAMED_IAM"
else
  pipenv run aws cloudformation describe-stacks \
    --stack-name ${stack_name} \
    --query 'Stacks[0].Outputs'
fi

