SHELL = /usr/bin/env bash -xeuo pipefail

.PHONY: \
	isort \
	lint \
	clean \
	deploy

isort:
	@isort -rc \
		src \
		tests

lint:
	@flake8 \
		src \
		tests

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

test-unit:
	# 01_base_resource/common
	PYTHONPATH=src/01_base_resource/common/python \
	python -m pytest tests/unit/01_base_resource/common

	# 03_alert_resource/notifier
	AWS_DEFAULT_REGION=ap-northeast-1 \
	AWS_ACCESS_KEY_ID=dummy \
	AWS_SECRET_ACCESS_KEY=dummy \
	PYTHONPATH=dummy/sar-aws-sns-to-slack/src/layers/python:src/01_base_resource/common/python:src/03_alert_resource/notifier \
		python -m pytest tests/unit/03_alert_resource/ingester --cov-config=setup.cfg --cov=src/03_alert_resource/notifier; \

	@for resource_dir in $$(find tests/unit -maxdepth 1 -type d); do \
		resource=$$(basename $$resource_dir); \
		if [[ $$resource =~ unit|__pycache__|fixtures|01_base_resource|03_alert_resource ]]; then continue; fi; \
		for handler_dir in $$(find $$resource_dir -maxdepth 1 -type d); do \
			handler=$$(basename $$handler_dir); \
			if [[ $$handler =~ __pycache__|$$resource ]]; then continue; fi; \
			AWS_DEFAULT_REGION=ap-northeast-1 \
			AWS_ACCESS_KEY_ID=dummy \
			AWS_SECRET_ACCESS_KEY=dummy \
			PYTHONPATH=src/01_base_resource/common/python:src/$$resource/$$handler \
				python -m pytest $$handler_dir --cov-config=setup.cfg --cov=src/$$resource/$$handler; \
		done \
	done
