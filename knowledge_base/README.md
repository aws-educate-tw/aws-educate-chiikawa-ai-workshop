# Amazon Bedrock Knowledge Base

建立 KB 時，存放區預設提供 ”Vector Store", "Structured Data Store", "Kendra GenAI index"。

我們預期應該都是塞 Markdown 格式的資料，選擇 "Vector Store"。

問題排查流程:

1. 建立 KB 後要手動 data sync，否則沒辦法跑 Test (這點不確定用 CloudFormation 建的話有沒有需要做)。
2. Sync 之後沒有出現問題，但 Test 時 LLM 只會回答 Sorry, I am not available to assist you 之類的回覆。
3. 因為沒有掛 Log，一開始一直找不到原因，以為是模型能力限制，後來重新建 KB 並在第一步掛 Log，就發現在 Ingestion 時就因為 S3 檔案超過 50 MB 而 ingest 失敗。
4. 跑程式分割之後，在 Semantic Chunking 遇到超過字元限制的問題，要在 Console 的 Warning 看 (CloudWatch 的 log 這時反而只會顯示 "Resource not processed due to a service exception. Please reach out to Amazon Bedrock technical support team...")。

## 透過 Console 建立 Knowledge Base (with vector store)

### 1. Choose data source type

- 設定 Knowledge Base name。
- 有 S3, Web Crawler 等，因資料和實作考量下就選擇 S3。
- 選擇 IAM policy
  - 缺少 RetrieveAndGenerate policy 不確定透過程式 access 是否需要。
- 記得設 Log deliveries，比較好排查錯誤。

### 2. Configure data source

- 選擇 S3 URI，到時候會需要 configure 外部 S3 URI 設 policy，AmazonBedrockKnowledgeBase 服務角色本身應該也需要設
- Parsing Strategy
  - Amazon Bedrock default parser 應該就可以處理簡單的 MD 檔。
- Chunking Strategy
  - Semantic chunking: 針對我們 case 的 MD 檔的處理方式。

- 關於選擇 parsing 和 chunking 策略的考量: https://claude.ai/share/6efb5fdd-caae-4e2e-9292-64fe852db82a

### 3. Configure data source and processing

- 選擇 Embeddings model: Titan Text Embeddings V2
- 選擇 Vector Database: Amazon OpenSearch Serverless (本來若是 CSV 的話有嘗試透過 Aurora PostgreSQL Serverless 建，不過後續 Test 遇到 Permission 相關問題)

### 4. Review

最後確認送出後，要記得按 Sync Data (**也就是說，沒有 sync data 的話，實際上向量資料庫是沒有資料的**)；到 CloudWatch 看發現 sync 實際會依序執行下列動作:

- Embedding started
- Embedding completed
- Indexing started
- Indexing completed

### CloudWatch 排查

- Ingestion 時每個檔案不能超過 50 MB 的限制
  ```json
  2025-04-04T12:24:43.048Z
  {
      "event_timestamp": 1743769483048,
      "event": {
          "ingestion_job_id": "XWEYRIG6EE",
          "document_location": {
              "type": "S3",
              "s3_location": {
                  "uri": "s3://cody-kb/output.md"
              }
          },
          "data_source_id": "TOCUDG5J8V",
          "status_reasons": [
              "Resource exceeded allowed size limit of 50 Megabytes. Please reduce the resource size and retry"
          ],
          "knowledge_base_arn": "arn:aws:bedrock:us-east-1:036109197688:knowledge-base/IYYX2VZGNA",
          "status": "RESOURCE_IGNORED"
      },
      "event_version": "1.0",
      "event_type": "StartIngestionJob.ResourceStatusChanged",
      "level": "WARN"
  }
  ```

- 跑腳本分割檔案 (每個檔案約 40 MB) 之後上傳，一樣在 Ingestion 時遇到問題，但這次 Log 只顯示 "Resource not processed due to a service exception. Please reach out to Amazon Bedrock technical support team..."
  - 後來回到 KB Console 看發現 data sync 時有 Warning 顯示 "Encountered error: File body text exceeds size limit of 1000000 for semantic chunking. [Files: s3://cody-kb/output_part8.md]. Call to Customer Source did not succeed."，看起來是檔案仍然太大，超過 Semantic Chunking 時的限制 (1,000,000 字元)。
  ```json
  2025-04-04T13:26:34.743Z
  {
      "event_timestamp": 1743773194743,
      "event": {
          "ingestion_job_id": "WKCWD2P9I9",
          "document_location": {
              "type": "S3",
              "s3_location": {
                  "uri": "s3://cody-kb/output_part1.md"
              }
          },
          "data_source_id": "53OSOWVLFJ",
          "status_reasons": [
              "Resource not processed due to a service exception. Please reach out to Amazon Bedrock technical support team for further assistance, or contact technical support at aws.amazon.com/contact-us/."
          ],
          "knowledge_base_arn": "arn:aws:bedrock:us-east-1:036109197688:knowledge-base/IYYX2VZGNA",
          "status": "RESOURCE_IGNORED"
      },
      "event_version": "1.0",
      "event_type": "StartIngestionJob.ResourceStatusChanged",
      "level": "WARN"
  }
  ```

- 手動分割檔案之後就沒遇到問題，Test 也能順利跑；接下來就可以時寫 tool 來看能不能真正使用 KB 中的資料做 RAG。

## 透過 CloudFormation 建立 Knowledge Base



## 參考資料

- [Knowledge Bases now delivers fully managed RAG experience in Amazon Bedrock](https://aws.amazon.com/blogs/aws/knowledge-bases-now-delivers-fully-managed-rag-experience-in-amazon-bedrock/)
- [Amazon Bedrock Knowledge Bases now supports custom prompts for the RetrieveAndGenerate API and configuration of the maximum number of retrieved results](https://aws.amazon.com/blogs/machine-learning/knowledge-bases-for-amazon-bedrock-now-supports-custom-prompts-for-the-retrieveandgenerate-api-and-configuration-of-the-maximum-number-of-retrieved-results/)
- [Build a RAG based Generative AI Chatbot in 20 mins using Amazon Bedrock Knowledge Base](https://www.youtube.com/watch?v=hnyDDfo8e9Q)
- [Knowledge Bases for Amazon Bedrock 在新增、刪除、修改檔案時 Vector Database 的變化](https://aws.amazon.com/tw/events/taiwan/techblogs/knowledge-bases-for-amazon-bedrock/)
- [Implement web crawling in Amazon Bedrock Knowledge Bases](https://aws.amazon.com/tw/blogs/machine-learning/implement-web-crawling-in-knowledge-bases-for-amazon-bedrock/)
- [Amazon Bedrock 知識庫資料的先決條件](https://docs.aws.amazon.com/zh_tw/bedrock/latest/userguide/knowledge-base-ds.html)
- [使用您為知識庫建立的向量存放區的先決條件](https://docs.aws.amazon.com/zh_tw/bedrock/latest/userguide/knowledge-base-setup.html)
- [AWS CloudFormation > AWS::Bedrock::KnowledgeBase](https://docs.aws.amazon.com/zh_tw/AWSCloudFormation/latest/UserGuide/aws-resource-bedrock-knowledgebase.html)
- [Bedrock Knowledgebase Agent Workload Iac](https://github.com/aws-samples/amazon-bedrock-rag-knowledgebases-agents-cloudformation)

### 檔案說明

Kaggle 上的資料集多半是 CSV 檔，做向量化效果可能不好，需要轉成 Markdown；加上因為 KB 使用 S3 作為 data source 的話有一些檔案上的限制，需要分割檔案。

不過分割後即便沒有超過檔案限制，在做 Chunking 時仍然可能超出 semantic chunking 的限制。

- [csv_to_md.py](csv_to_md.py): 將 Kaggle 資料集轉換為 Markdown，方便上傳 S3 作為 Bedrock Knowledge Base 的 data source（因 S3 檔案大小限制，須再經過切分）。
  - 使用: `python csv_to_md.py </path/to/csv_file> </path/to/outout_md> --fields [reserved fields splited by space]` 
  - e.g. `python csv_to_md.py TMDB_movies.csv output.md --fields title overview genres keywords`
- [split_markdown.py](split_markdown.py): 將轉換成 MD 格式的資料集切分，以符合 Bedrock Knowledge Base data source 的限制。
  - 使用: `python split_markdown.py </path/to/output_md> --max-size [target size] --outout-dir <destination folder>`
  - e.g. `python split_markdown.py output.md --max-size 40 --output-dir movies`

## 資料集來源

- Movies
  - [Full TMDB Movies Dataset 2024 (1M Movies)](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies): TMDB_movie_dataset_v11.csv(546.2 MB)
  - [The Ultimate 1Million Movies Dataset (TMDB + IMDb)](https://www.kaggle.com/datasets/alanvourch/tmdb-movies-daily-updates/data): TMDB_all_movies.csv(645.12 MB)
- Books
  - Not yet.
- Psy_test
  - [Netflix影史最受歡迎的10部英語電影！觀看次數最高的片單全都在這裡](https://www.gvm.com.tw/article/120358)