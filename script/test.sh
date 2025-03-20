#!/usr/bin/zsh

# API Gateway call
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' \
  https://m70mzlgjd7.execute-api.us-west-2.amazonaws.com/test/webhook