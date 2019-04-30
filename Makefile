SHELL = /usr/bin/env bash -xeuo pipefail

.PHONY: \
	isort \
	lint \
	clean \
	deploy

isort:
	@isort -rc \
		src

lint:
	@flake8 \
		src

clean:
	@find src/** -type d \( -name '__pycache__' -o -name '*\.dist-info' -o -name '*\.egg-info' \) -print0 | xargs -0 -n1 rm -rf
	@find src/** -type f \( -name '.coverage' -o -name '*.pyc' \) -print0 | xargs -0 -n1 rm -rf

deploy: clean
	@aws cloudformation package \
		--template-file template.yml \
		--s3-bucket bibl-cfn-artifacts-$(AWS_ACCOUNT_ID)-$(AWS_ENV) \
		--output-template-file packaged_template.yml
	@aws cloudformation deploy \
		--template-file packaged_template.yml \
		--stack-name artilf-api-$(AWS_ENV) \
		--role-arn $(AWS_CFN_DEPLOY_ROLE_ARN) \
		--capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
		--no-fail-on-empty-changeset
