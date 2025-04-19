import unittest
from unittest.mock import MagicMock, patch
import os
os.environ['LANGSMITH_TRACING'] = "false"
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from config.settings import settings
from logger import set_logger
set_logger(env="prod", name=settings.TEST_LOG_NAME)
from graph.graph_builder import Graph
from graph.state import State
from graph.nodes import query_analyzer_node, retrieval_node, augmentation_node, final_response_node
from services.prompt_manager import PromptManager
from services.llm_provider import LLMProvider
from services.llm_chain_factory import LLMChainFactory
from clients.embedding_client import EmbeddingClient
from clients.pinecone_client import PineconeClient
from langchain_google_genai import ChatGoogleGenerativeAI


class TestServices(unittest.TestCase):
    def setUp(self):
        """Set up mocks for all dependencies."""
        # Mock LLM and LLMProvider
        
        LLMProvider._instance = None
        LLMProvider._llm = None
        PromptManager._instance = None

        self.logger_patcher = patch("services.llm_provider.logger")
        self.mock_logger = self.logger_patcher.start()

        self.chat_llm_patcher = patch('services.llm_provider.ChatGoogleGenerativeAI')
        self.mock_chat_llm = self.chat_llm_patcher.start()

        # Set up a mocked instance of ChatGoogleGenerativeAI
        self.mock_llm_instance = MagicMock(spec=ChatGoogleGenerativeAI)
        self.mock_chat_llm.return_value = self.mock_llm_instance
        # Mock structured output for the LLM
        self.mock_llm_instance.with_structured_output.return_value = MagicMock()

        # Initialize LLMProvider with test values
        self.mock_llm_provider = LLMProvider(api_key="test_api_key", model_name="test_model")
        # self.llm_provider.get_llm.return_value = self.mock_llm_instance
        self.mock_llm_provider.get_llm = MagicMock(return_value=self.mock_llm_instance)
        

        # Patch settings
        self.settings_patcher = patch('services.prompt_manager.settings')
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.prompt_setting.project_id = 'test_project_id'
        self.mock_settings.prompt_setting.prompt_mapping = {'test_prompt': ('test_prompt_id', 'test_prompt_version')}

        # Patch vertexai.init
        self.vertexai_patcher = patch('services.prompt_manager.vertexai.init')
        self.mock_vertexai_init = self.vertexai_patcher.start()

        # Patch prompts.list and prompts.get
        self.prompts_list_patcher = patch('services.prompt_manager.prompts.list')
        self.mock_prompts_list = self.prompts_list_patcher.start()

        self.prompts_get_patcher = patch('services.prompt_manager.prompts.get')
        self.mock_prompts_get = self.prompts_get_patcher.start()

        # Mock prompt responses
        self.mock_prompt = MagicMock()
        self.mock_prompt.prompt_id = 'test_prompt_id'
        self.mock_prompt.version_id = 'test_prompt_version'
        self.mock_prompts_list.return_value = [self.mock_prompt]
        self.mock_prompts_get.return_value.prompt_data = 'Mocked prompt data'

        # Initialize the PromptManager
        self.prompt_manager = PromptManager()

        self.prompt_template_patcher = patch('services.llm_chain_factory.PromptTemplate')
        self.mock_prompt_template = self.prompt_template_patcher.start()

        # self.chat_prompt_template_patcher = patch('services.llm_chain_factory.PromptTemplate')
        # self.mock_chat_prompt_template = self.chat_prompt_template_patcher.start()


        # Initialize LLMChainFactory with the mocked LLMProvider
        self.chain_factory = LLMChainFactory(self.mock_llm_provider)

    def tearDown(self):
        # Add cleanup to stop patches
        self.addCleanup(self.chat_llm_patcher.stop)
        self.addCleanup(self.settings_patcher.stop)
        self.addCleanup(self.vertexai_patcher.stop)
        self.addCleanup(self.prompts_list_patcher.stop)
        self.addCleanup(self.prompts_get_patcher.stop)
        self.addCleanup(self.prompt_template_patcher.stop)
        self.addCleanup(self.logger_patcher.stop)
        # self.addCleanup(self.chat_prompt_template_patcher.stop)

    # @patch("services.llm_provider.logger")
    def test_singleton_behavior(self):
        """Test that LLMProvider is a singleton and returns the same instance."""
        another_instance = LLMProvider(api_key="new_key", model_name="new_model")
        another_prompt_instance = PromptManager()
        # self.assertIs(self.mock_llm_provider, another_instance, "LLMProvider should be a singleton.")
        self.assertEqual(id(self.mock_llm_provider), id(another_instance), "LLMProvider should be a singleton.")
        self.assertEqual(id(self.prompt_manager), id(another_prompt_instance), "PromptManager should be a singleton.")

    # @patch("services.llm_provider.logger")
    def test_llm_provider_init(self):
        """Test that LLMProvider initializes ChatGoogleGenerativeAI with correct parameters."""
        self.mock_chat_llm.assert_called_once_with(api_key="test_api_key", model="test_model")

    # @patch("services.llm_provider.logger")
    def test_get_llm(self):
        """Test that get_llm returns the initialized LLM instance."""
        llm_instance = self.mock_llm_provider.get_llm()
        self.assertEqual(llm_instance, self.mock_llm_instance, "get_llm should return the mocked LLM instance.")

    def test_prompt_manager_init(self):
        # Assertions to verify behaviors
        self.mock_vertexai_init.assert_called_once_with(project='test_project_id')
        self.mock_prompts_list.assert_called_once()

    def test_get_prompt(self):
        # Test the get_prompt method
        prompt_data = self.prompt_manager.get_prompt('test_prompt')
        self.assertEqual(prompt_data, 'Mocked prompt data')

    # @patch("services.llm_chain_factory.logger")
    def test_create_query_analysis_chain(self):
        """Test create_query_analysis_chain in LLMChainFactory."""
        mock_output_model = MagicMock()

        result = self.chain_factory.create_query_analysis_chain("Test prompt", mock_output_model)

        # Check if PromptTemplate was created correctly
        self.mock_prompt_template.assert_called_once_with(input_variables=["conversation", "query"], template="Test prompt")

        # Ensure get_llm() was called
        self.mock_llm_instance.with_structured_output.assert_called_once_with(mock_output_model, include_raw=True)

        # Ensure the return value was piped correctly
        self.assertIsNotNone(result, "The query analysis chain should not be None")

    # @patch("services.llm_chain_factory.logger")
    def test_create_final_response_chain(self):
        """Test create_final_response_chain in LLMChainFactory."""
        system_prompt = "Test system prompt"

        result = self.chain_factory.create_final_response_chain(system_prompt)

        # Check if ChatPromptTemplate was created correctly

        self.mock_prompt_template.assert_called_once_with(input_variables=["conversation_history", "user_query", "retrieved_context"], template="Test system prompt")
        
        # Ensure get_llm() was called
        self.mock_llm_provider.get_llm.assert_called_once()

        # Ensure the return value was piped correctly
        self.assertIsNotNone(result, "The final response chain should not be None")


if __name__ == "__main__":
    unittest.main()
