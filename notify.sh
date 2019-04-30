#!/usr/bin/env bash

export LC_ALL=C.UTF-8

status=""
icon=""

while getopts ':sef' args; do
  case ${args} in
    s)
      status="start"
      icon=":circleci:"
      ;;
    e)
      status="success"
      icon=":circleci_success:"
      ;;
    f)
      status="failed"
      icon=":circleci_failed:"
      ;;
  esac
done

endpoint="$SLACK_INCOMMING_WEBHOOK_URL"
text="リポジトリ: ${CIRCLE_REPOSITORY_URL}\nブランチ/タグ: ${CIRCLE_BRANCH}${CIRCLE_TAG}\nジョブ: ${CIRCLE_JOB}\nステータス: ${status}\nビルドURL: ${CIRCLE_BUILD_URL}"
payload="{\"username\": \"$status\", \"text\": \"$text\", \"icon_emoji\": \"$icon\"}"

curl -X POST --data-urlencode "payload=$payload" ${endpoint}
