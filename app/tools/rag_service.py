import os
import boto3
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain_aws import ChatBedrock
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

model_id = "meta.llama3-70b-instruct-v1:0"
knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")

class RagQueryArgs(BaseModel):
    query: str = Field(description="The query to search the knowledge base")
    max_results: int = Field(description="The maximum number of results to return", default=5)

class RagService:
    def __init__(self):
        self.knowledge_base_id = knowledge_base_id
        self.model_id = model_id
        self.retriever = None
        self.qa_chain = None
        self._initialize_retriever()
        self._initialize_qa_chain()

    def _initialize_retriever(self):
        self.retriever = AmazonKnowledgeBasesRetriever(
            knowledge_base_id=self.knowledge_base_id,
            retrieval_config={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5  # Discussible
                }
            }
        )

    def _initialize_qa_chain(self):
        llm = ChatBedrock(
            model_id=self.model_id,
            model_kwargs={"temperature": 0}
        )

        template = """你是一位戀愛顧問機器人，請以簡單且直接的方式回答與戀愛心理相關的問題。
        
        請使用以下搜尋到的訊息來回答使用者的問題。如果搜尋到的訊息不足以回答問題，請明白說明你沒有足夠的訊息，不需要編造答案。
        
        請以溫暖、親切但專業的語氣回答，讓使用者感到被理解和受到重視。所有回覆必須使用繁體中文。
        
        搜尋到的訊息：
        {context}
        
        使用者的問題：{question}
        
        回覆："""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

    def query(self, query: str, max_results: int = 5):
        """RAG query"""
        logger.info(f"Querying knowledge base with query: {query}")
        if not self.qa_chain:
            raise ValueError("RAG chain not initialized")
        
        self.retriever.retrieval_config.vectorSearchConfiguration.numberOfResults = max_results

        result = self.qa_chain({"query": query})
        print("result", result)

        response = {
            "answer": result["result"],
        }

        return response

def query_knowledge_base(query: str, max_results: int = 5):
    """Wrapper function for the RAG service query"""
    logger.info("RAG tool called.")
    _rag_service = RagService()
    return _rag_service.query(query, max_results)

__all__ = ['query_knowledge_base', 'RagQueryArgs']