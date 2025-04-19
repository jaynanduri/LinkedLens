from clients.embedding_client import EmbeddingClient
import re
from typing import Literal

class RAGEvaluator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.embedding_client = EmbeddingClient()
        return cls._instance

    def _clean_text_for_similarity(self, text: str, source: Literal["context", "response"]) -> str:
        # Common cleaning for all types
        print(f"Cleaning text for Source: {source}")
        text = re.sub(r'\[.*?\]\(https?://[^\s)]+\)', '', text) # [label](url)
        text = re.sub(r'https?://[^\s,)\]]+', '', text) # raw URLs
        text = re.sub(r'\[[^\]]*?\]', '', text) # [Recruiter Post] etc.
        text = re.sub(r'\b(Source|Author|Job):\s*https?://[^\s,)\]]+[,)]?', '', text)  # headings + URLs
        text = re.sub(r'\b(Source|Author|Job):\s*', '', text) # remaining headings
        text = re.sub(r'\(\s*\)', '', text) # empty parentheses

        if source == "context":
            text = re.sub(r'Author Profile URL: https?://[^\s,]+,?\s*', '', text)
            text = re.sub(r'Job URL: https?://[^\s,]+,?\s*', '', text)
            text = re.sub(r'Source: https?://[^\s,]+,?\s*', '', text)
            text = re.sub(r'Relevance: \d+(\.\d+)?[,]?\s*', '', text)
            text = re.sub(r'\[Metadata\]\s*', '', text)
            text = re.sub(r'\[Content\]\s*', '', text)

        # Cleanup
        text = re.sub(r',\s*,+', ',', text)
        text = re.sub(r',\s*\n', '\n', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r'\n{2,}', '\n\n', text)
        text = re.sub(r' ,', ',', text)

        return text.strip()

    def evaluate(self, query: str, standalone_query: str, context: str, response: str) -> dict:
        cleaned_context = self._clean_text_for_similarity(context, source="context")
        cleaned_response = self._clean_text_for_similarity(response, source="response")
        metrics = {
            "retrieval_relevance": None,
            "response_relevance": None,
            "faithfulness": None
        }

        metrics["response_relevance"] = self.embedding_client.cos_sim(query, cleaned_response)
        metrics["faithfulness"] = self.embedding_client.cos_sim(context, response)
        if cleaned_context.strip():
            metrics["retrieval_relevance"] = self.embedding_client.cos_sim(
                standalone_query, cleaned_context
            )
            

        return metrics