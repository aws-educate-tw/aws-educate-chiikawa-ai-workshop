# Use CloudFormation to deploy your LINE Bot

1. 用 `deploy/template.yaml` 貼上到 CloudFormation 的 Infrastructure Composer，並 validate 接著 create template
2. 建立 Stack，並填入 LINE Bot 需要的兩個環境變數
3. 接下來設定都先不動，Next 直到 create stack
4. 再來就等資源都部上去，主要是 API Gateway 和 Lambda
5. 等待期間可以先建立 Zip 等等要上傳到 Lambda 用

## 建立 Zip

1. `cd app`
2. `mkdir -p python/lib/python3.11/site-packages`
3. `pip install -r requirements.txt --platform manylinux2014_x86_64 -t python/lib/python3.11/site-packages --implementation cp --python-version 3.11 --only-binary=:all:`
4. `zip -r line-bot-layer.zip python`

## 回到 AWS Console

1. 到 Lambda 找剛建立的 function ("auto-chiikawa-linebot")
2. 點進去，上傳剛建立的 Zip 檔 (`line-bot-layer.zip`)
3. 到 API Gateways 找剛建立的 API ("auto-chiikawa-api")
4. 點選 Stages，找到 Invoke URL 複製
5. 到 LINE Developer 貼上

完成！應該就可以透過 Cloudformation 建立我們要的 LINE Bot 了，其中沒那麼自動化的部分剩上傳 Zip，之後看要不要改成用 S3。

## Docker Deployment

我目前在自己的 AWS 帳號建 ECR 上傳 LINE Bot webhook handler 的 image，然後在 CloudFormation 指定我們的 Lambda 要使用該 image。

在專案根目錄，執行下列命令：

1. `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 423623870189.dkr.ecr.us-east-1.amazonaws.com`
2. `docker build --build-arg MAP_API_KEY=[MAP_API_KEY] --build-arg WEATHER_API_KEY=[WEATHER_API_KEY] -t chiikawa-linebot-webhook-handler .`
3. `docker tag chiikawa-linebot-webhook-handler 423623870189.dkr.ecr.us-east-1.amazonaws.com/2025-aws-chiikawa-ai-workshop:chiikawa-linebot-webhook-handler`
4. `docker push 423623870189.dkr.ecr.us-east-1.amazonaws.com/2025-aws-chiikawa-ai-workshop:chiikawa-linebot-webhook-handler`

P.S. 前面建立 zip 的步驟就可以省略，直接在 CloudFormation 階段把服務都弄好，後續不需要再上傳 code。
