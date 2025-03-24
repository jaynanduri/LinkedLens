from langchain_google_genai import ChatGoogleGenerativeAI

class LLMProvider:
    _instance = None
    _llm = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LLMProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: str, model_name: str):
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(api_key=api_key, model=model_name)

    def get_llm(self):
        return self._llm