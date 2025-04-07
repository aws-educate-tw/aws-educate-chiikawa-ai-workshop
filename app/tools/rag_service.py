import boto3
import os
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain_aws import ChatBedrock
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import logging
from typing import Optional, Dict, Any
from botocore.exceptions import BotoCoreError, ClientError
import time
from functools import wraps

logger = logging.getLogger()
logger.setLevel(logging.INFO)

model_id = "meta.llama3-70b-instruct-v1:0"
knowledge_base_id = os.getenv("KNOWLEDGE_BASE_ID")

# 自定義異常類別
class RAGServiceError(Exception):
    """Base exception class for RAG service errors"""
    pass

class KnowledgeBaseInitError(RAGServiceError):
    """Raised when knowledge base initialization fails"""
    pass

class QueryProcessingError(RAGServiceError):
    """Raised when query processing fails"""
    pass

class ModelError(RAGServiceError):
    """Raised when LLM encounters an error"""
    pass

# 重試裝飾器
def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1,
    exponential_base: float = 2,
    max_delay: float = 10
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for retry in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (BotoCoreError, ClientError) as e:
                    if retry == max_retries - 1:
                        logger.error(f"Max retries ({max_retries}) reached. Final error: {str(e)}")
                        raise
                    logger.warning(f"Attempt {retry + 1} failed: {str(e)}. Retrying...")
                    time.sleep(min(delay, max_delay))
                    delay *= exponential_base
            return func(*args, **kwargs)
        return wrapper
    return decorator

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
        try:
            logger.info("Initializing knowledge base retriever...")
            self.retriever = AmazonKnowledgeBasesRetriever(
                knowledge_base_id=self.knowledge_base_id,
                retrieval_config={
                    "vectorSearchConfiguration": {
                        "numberOfResults": 5
                    }
                }
            )
            logger.info("Knowledge base retriever initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {str(e)}")
            raise KnowledgeBaseInitError(f"Retriever initialization failed: {str(e)}")

    def _initialize_qa_chain(self):
        llm = ChatBedrock(
            model_id=self.model_id,
            model_kwargs={"temperature": 0}
        )

        template = """你是一位戀愛顧問機器人，請以簡單且直接的方式回答與戀愛心理相關的問題。
        
        請使用以下搜尋到的信息來回答用戶的問題。如果搜尋到的訊息不足以回答問題，請明白說明你沒有足夠的訊息，不需要編造答案。
        
        請以溫暖、親切但專業的語氣回答，讓用戶感到被理解和受到重視。所有回覆必須使用繁體中文。
        
        搜尋到的訊息或文件：
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
            logger.info("QA chain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize QA chain: {str(e)}")
            raise KnowledgeBaseInitError(f"QA chain initialization failed: {str(e)}")

    @retry_with_exponential_backoff()
    def query(self, args: RagQueryArgs) -> Dict[str, Any]:
        """RAG query with error handling and logging"""
        logger.info(f"Processing RAG query: {args.query}")

        try:
            if not self.qa_chain:
                raise QueryProcessingError("RAG chain not initialized")
            
            if not args.query.strip():
                raise ValueError("Query cannot be empty")
            
            if args.max_results < 1:
                raise ValueError("max_results must be greater than 0")

            self.retriever.retrieval_config["vectorSearchConfiguration"]["numberOfResults"] = args.max_results

            result = self.qa_chain({"query": args.query})

            response = {
                "answer": result.get("answer", "No answer generated"),
                "sources": [doc.metadata.get("source", "Unknown") for doc in result.get("source_documents", [])],
                "status": "success"
            }

            logger.info(f"Query processed successfully. Found {len(response['sources'])} sources")
            return response

        except ValueError as e:
            logger.error(f"Invalid input parameters: {str(e)}")
            return {
                "answer": f"查詢參數錯誤：{str(e)}",
                "sources": [],
                "status": "error",
                "error_type": "validation_error"
            }

        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS service error: {str(e)}")
            return {
                "answer": "抱歉，查詢服務暫時無法使用，請稍後再試。",
                "sources": [],
                "status": "error",
                "error_type": "aws_service_error"
            }

        except Exception as e:
            logger.error(f"Unexpected error during query processing: {str(e)}")
            return {
                "answer": "處理查詢時發生意外錯誤，請稍後重試。",
                "sources": [],
                "status": "error",
                "error_type": "unexpected_error"
            }

_rag_service = RagService()

def query_knowledge_base(args: RagQueryArgs) -> Dict[str, Any]:
    """Wrapper function for the RAG service query with error handling"""
    try:
        logger.info(f"RAG tool called with query: {args.query}")
        return _rag_service.query(args)
    except Exception as e:
        logger.error(f"Error in query_knowledge_base wrapper: {str(e)}")
        return {
            "answer": "很抱歉，知識庫查詢服務暫時無法使用。請稍後再試。",
            "sources": [],
            "status": "error",
            "error_type": "service_error"
        }

__all__ = ['query_knowledge_base', 'RagQueryArgs']