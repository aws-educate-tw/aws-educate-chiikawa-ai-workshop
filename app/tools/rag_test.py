from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain_aws import ChatBedrock

model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
knowledge_base_id = "NK8AUITM03"

retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=knowledge_base_id,
    retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
)

llm = ChatBedrock(model_id=model_id, region_name="us-east-1")

query = "Recommend some superhero movies"

retrieved_docs = retriever.invoke(query)

context = "\n\n".join([doc.page_content for doc in retrieved_docs])

prompt = f"""
請根據以下資訊回答問題。如果無法從資訊中找到答案，請直接說你不知道，不要編造資訊。

資訊：
{context}

問題：{query}

回答：
"""

response = llm.invoke(prompt)

print(response)