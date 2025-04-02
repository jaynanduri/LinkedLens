import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from unittest.mock import patch, MagicMock
from graph.graph_builder import Graph
from graph.state import State
import torch
from mock_classes import *
from functools import partial
from graph.nodes import *
from clients.embedding_client import EmbeddingClient
from clients.pinecone_client import PineconeClient
from langchain.schema import HumanMessage, AIMessage
from services.llm_chain_factory import LLMChainFactory
from services.llm_provider import LLMProvider
from services.prompt_manager import PromptManager


class TestGraph(unittest.TestCase):
    def setUp(self):
        """Set up mocks for dependencies."""

        self.mock_embedding_client = MagicMock(spec=EmbeddingClient)
        self.mock_pinecone_client = MagicMock(spec=PineconeClient)

        self.mock_pinecone_client.query_similar = MagicMock(
            side_effect=lambda query_vector, top_k, namespace, filter, include_metadata, include_values: 
                {"matches": [
                    {"id": "job_doc1", "score": 0.92, "metadata": {"text": "Job market trends."}},
                    {"id": "job_doc2", "score": 0.88, "metadata": {"text": "Resume tips for AI jobs."}},
                ]} if namespace == "job" else 
                {"matches": [
                    {"id": "recruiter_doc1", "score": 0.90, "metadata": {"text": "How recruiters hire AI talent."}},
                    {"id": "recruiter_doc2", "score": 0.85, "metadata": {"text": "Recruiter insights on hiring trends."}},
                ]} if namespace == "recruiter_post" else {"matches": []}
        )

        self.mock_embedding_client.generate_embedding = MagicMock(return_value=torch.ones(384))

        # Mock settings
        self.mock_settings_patcher = patch('graph.nodes.settings')
        self.mock_settings = self.mock_settings_patcher.start()
        self.mock_settings.pinecone.max_docs = 2
        self.mock_settings.pinecone.namesapce_threshold = {"recruiter_post": 0.8, "job": 0.7}
        self.mock_settings.NAMESPACE_URLS = {'job': 'https://example.com/jobs'}
        self.mock_settings.GEMINI_API_KEY = "fake_api_key"
        self.mock_settings.GEMINI_MODEL_NAME = "gemini-model"

        self.mock_chain = MagicMock()
        
        self.state = State(
            query="What is AI?",
            standalone_query="What is artificial intelligence?",
            query_type="retrieve",
            vector_namespace=["job", "recruiter_post"],
            retrieved_docs=[],
            final_context="",
            response="",
            messages=[HumanMessage(content="Hello"), AIMessage(content="Hi!")]
        )

        # Mock StateGraph
        self.mock_state_graph_patcher = patch("graph.graph_builder.StateGraph")
        self.mock_state_graph = self.mock_state_graph_patcher.start()
        self.mock_builder = MagicMock()
        self.mock_state_graph.return_value = self.mock_builder

        # Mock LLM components
        self.mock_llm_provider = MagicMock(spec=LLMProvider)
        self.mock_chain_factory = MagicMock(spec=LLMChainFactory)
        self.mock_prompt_manager = MagicMock(spec=PromptManager)

        # Mock chain creation
        self.mock_chain_factory.create_query_analysis_chain.return_value = MagicMock()
        self.mock_chain_factory.create_final_response_chain.return_value = MagicMock()

        # Mock prompt manager
        self.mock_prompt_manager.get_prompt.side_effect = lambda name: f"Mocked {name}"

        # Patch the LLMProvider, LLMChainFactory, PromptManager in the Graph class
        self.mock_llm_provider_patcher = patch("graph.graph_builder.LLMProvider", return_value=self.mock_llm_provider)
        self.mock_chain_factory_patcher = patch("graph.graph_builder.LLMChainFactory", return_value=self.mock_chain_factory)
        self.mock_prompt_manager_patcher = patch("graph.graph_builder.PromptManager", return_value=self.mock_prompt_manager)

        self.mock_llm_provider_patcher.start()
        self.mock_chain_factory_patcher.start()
        self.mock_prompt_manager_patcher.start()

        # Create the Graph instance
        self.graph = Graph()

    def tearDown(self):
        # Stop each patcher individually
        self.mock_settings_patcher.stop()
        self.mock_state_graph_patcher.stop()
        self.mock_llm_provider_patcher.stop()
        self.mock_chain_factory_patcher.stop()
        self.mock_prompt_manager_patcher.stop()

    def test_initialize_components(self):
        """Test if components are initialized correctly in Graph."""
        self.assertIsInstance(self.graph.llm_provider, LLMProvider)
        self.assertIsInstance(self.graph.chain_factory, LLMChainFactory)
        self.assertIsInstance(self.graph.prompt_manager, PromptManager)
        
        self.mock_prompt_manager.get_prompt.assert_any_call("query_analysis_prompt")
        self.mock_prompt_manager.get_prompt.assert_any_call("final_system_prompt")
        
        self.mock_chain_factory.create_query_analysis_chain.assert_called_once()
        self.mock_chain_factory.create_final_response_chain.assert_called_once()

        self.assertIsInstance(self.mock_embedding_client, EmbeddingClient)
        self.assertIsInstance(self.mock_pinecone_client, PineconeClient)


    def test_build_graph(self):
        """Test build_graph constructs the correct workflow."""
        self.graph.build_graph(isMemory=False)

        # Verify nodes are added
        added_nodes = self.mock_builder.add_node.call_args_list
        expected_nodes = [
            ("query_analyzer_node", partial(query_analyzer_node, chain=self.graph.query_analysis_chain)),
            ("retrieval_node", partial(retrieval_node, embedding_client=self.graph.embedding_client, pinecone_client=self.graph.pinecone_client)),
            ("augmentation_node", partial(augmentation_node, pinecone_client=self.graph.pinecone_client)),
            ("final_response_node", partial(final_response_node, chain=self.graph.final_response_chain))
        ]

        for expected_name, expected_func in expected_nodes:
            assert any(call[0][0] == expected_name for call in added_nodes), f"Node {expected_name} was not added."

        # Verify edges
        self.mock_builder.add_edge.assert_any_call("__start__", "query_analyzer_node")
        self.mock_builder.add_conditional_edges.assert_called_once()
        self.mock_builder.add_edge.assert_any_call("retrieval_node", "augmentation_node")
        self.mock_builder.add_edge.assert_any_call("augmentation_node", "final_response_node")
        self.mock_builder.add_edge.assert_any_call("final_response_node", "__end__")

        # Verify graph compilation
        self.mock_builder.compile.assert_called_once_with()


    def test_query_analyzer_node_success(self):
        """Test query_analyzer_node function when chain.invoke succeeds."""
        # Mock successful LLM response
        mock_parsed_result = MagicMock()
        mock_parsed_result.standalone_query = "What is AI?"
        mock_parsed_result.query_type = "retrieve"
        mock_parsed_result.vector_namespace = ["user"]

        self.mock_chain.invoke.return_value = {"parsed": mock_parsed_result}

        # Run the function
        result = query_analyzer_node(self.state, self.mock_chain)

        # Assertions
        self.assertEqual(result["standalone_query"], "What is AI?")
        self.assertEqual(result["query_type"], "retrieve")
        self.assertEqual(result["vector_namespace"], ["user"])

    def test_query_analyzer_node_success_generic(self):
        """Test query_analyzer_node when LLM returns query_type as 'generic'."""
        mock_parsed_result = MagicMock()
        mock_parsed_result.standalone_query = self.state["query"]
        mock_parsed_result.query_type = "generic"
        mock_parsed_result.vector_namespace = [] 

        self.mock_chain.invoke.return_value = {"parsed": mock_parsed_result}

        result = query_analyzer_node(self.state, self.mock_chain)

        self.assertEqual(result["standalone_query"], self.state["query"]) 
        self.assertEqual(result["query_type"], "generic")
        self.assertEqual(result["vector_namespace"], [])

    def test_query_analyzer_node_exception(self):
        """Test query_analyzer_node function when chain.invoke raises an exception."""
        self.mock_chain.invoke.side_effect = Exception("Mocked error")

        # Run the function
        result = query_analyzer_node(self.state, self.mock_chain)

        # Assertions: Expecting fallback values
        self.assertEqual(result["standalone_query"], self.state["query"])
        self.assertEqual(result["query_type"], "retrieve")
        self.assertEqual(result["vector_namespace"], ["user", "job", "user_post", "recruiter_post"])


    def test_check_query_type_retrieve(self):
        """Test check_query_type when query_type is 'retrieve'."""
        state = State(query_type="retrieve") 
        result = check_query_type(state)
        self.assertEqual(result, "retrieve")

    def test_check_query_type_generic(self):
        """Test check_query_type when query_type is 'generic'."""
        state = State(query_type="generic") 
        result = check_query_type(state)
        self.assertEqual(result, "generic")


    def test_retrieval_node_single_namespace_job(self):
        """Test retrieval_node retrieves documents correctly for 'job' namespace."""
        # self.state.vector_namespace = ["job"]  # Set namespace to 'job'
        self.state["vector_namespace"] = ["job"]
        result = retrieval_node(self.state, self.mock_embedding_client, self.mock_pinecone_client)

        expected_docs = [
            {"id": "job_doc1", "score": 0.92, "metadata": {"text": "Job market trends."}},
            {"id": "job_doc2", "score": 0.88, "metadata": {"text": "Resume tips for AI jobs."}},
        ]

        self.assertIn("retrieved_docs", result)
        self.assertEqual(result["retrieved_docs"], expected_docs)


    def test_retrieval_node_single_namespace_recruiter_post(self):
        """Test retrieval_node retrieves documents correctly for 'recruiter_post' namespace."""
        # self.state.vector_namespace = ["recruiter_post"]  # Set namespace to 'recruiter_post'
        self.state["vector_namespace"] = ["recruiter_post"]
        result = retrieval_node(self.state, self.mock_embedding_client, self.mock_pinecone_client)

        expected_docs = [
            {"id": "recruiter_doc1", "score": 0.90, "metadata": {"text": "How recruiters hire AI talent."}},
            {"id": "recruiter_doc2", "score": 0.85, "metadata": {"text": "Recruiter insights on hiring trends."}},
        ]

        self.assertIn("retrieved_docs", result)
        self.assertEqual(result["retrieved_docs"], expected_docs)


    def test_retrieval_node_multiple_namespaces(self):
        """Test retrieval_node retrieves documents from multiple namespaces."""
        # self.state.vector_namespace = ["job", "recruiter_post"]  # Both namespaces
        self.state["vector_namespace"] = ["job", "recruiter_post"]
        result = retrieval_node(self.state, self.mock_embedding_client, self.mock_pinecone_client)

        expected_docs = [
            {"id": "job_doc1", "score": 0.92, "metadata": {"text": "Job market trends."}},
            {"id": "job_doc2", "score": 0.88, "metadata": {"text": "Resume tips for AI jobs."}},
            {"id": "recruiter_doc1", "score": 0.90, "metadata": {"text": "How recruiters hire AI talent."}},
            {"id": "recruiter_doc2", "score": 0.85, "metadata": {"text": "Recruiter insights on hiring trends."}},
        ]

        self.assertIn("retrieved_docs", result)
        self.assertEqual(result["retrieved_docs"], expected_docs)


    def test_retrieval_node_no_matches(self):
        """Test retrieval_node when no matches are returned from Pinecone."""
        self.mock_pinecone_client.query_similar = MagicMock(return_value={"matches": []})
        # self.state.vector_namespace = ["job"]  # Any namespace
        self.state["vector_namespace"] = ["job"]
        result = retrieval_node(self.state, self.mock_embedding_client, self.mock_pinecone_client)

        expected_docs = []  # No results expected

        self.assertIn("retrieved_docs", result)
        self.assertEqual(result["retrieved_docs"], expected_docs)


    def test_retrieval_node_with_threshold_filtering(self):
        """Test retrieval_node where some results are below the threshold and get filtered out."""
        self.mock_pinecone_client.query_similar = MagicMock(return_value={
            "matches": [
                {"id": "doc_high", "score": 0.9, "metadata": {"text": "High-score document."}},  # Above threshold
                {"id": "doc_low", "score": 0.4, "metadata": {"text": "Low-score document."}},  # Below threshold
            ]
        })
        # self.state.vector_namespace = ["job"]  # Use 'job' with threshold 0.7
        self.state["vector_namespace"] = ["job"]
        result = retrieval_node(self.state, self.mock_embedding_client, self.mock_pinecone_client)

        expected_docs = [
            {"id": "doc_high", "score": 0.9, "metadata": {"text": "High-score document."}},  # Only this should remain
        ]

        self.assertIn("retrieved_docs", result)
        self.assertEqual(result["retrieved_docs"], expected_docs)

    def test_fetch_complete_doc_text(self):
        """Test fetch_complete_doc_text aggregates document chunks correctly."""
        
        # Mock matches input
        matches = [
            {
                "id": "job123_chunk_1",
                "score": 0.92,
                "metadata": {
                    "firestoreId": "job123",
                    "docType": "job",
                    "chunk": 1,
                    "total_chunks": 2,
                    "raw_data": "This is chunk one."
                }
            },
            {
                "id": "job123_chunk_2",
                "score": 0.90,
                "metadata": {
                    "firestoreId": "job123",
                    "docType": "job",
                    "chunk": 2,
                    "total_chunks": 2,
                    "raw_data": "This is chunk two."
                }
            },
            {
                "id": "job456_chunk_1",
                "score": 0.87,
                "metadata": {
                    "firestoreId": "job456",
                    "docType": "job",
                    "chunk": 1,
                    "total_chunks": 2,
                    "raw_data": "This is chunk one."
                }
            },
            {
                "id": "job456_chunk_2",
                "score": 0.85,
                "metadata": {
                    "firestoreId": "job456",
                    "docType": "job",
                    "chunk": 2,
                    "total_chunks": 2,
                    "raw_data": "This is chunk two."
                }
            }
        ]

        # Mock return values from Pinecone fetch call
        def mock_fetch_by_vector_ids(vector_id_list, namespace):
            # Create mock vectors with correct metadata
            vectors = {
                vector_id: {
                    "firestoreId": vector_id.split("_")[0],  # Extract job ID
                    "chunk": int(vector_id.split("_")[-1]),  # Convert chunk number to int
                    "raw_data": f"This is chunk {vector_id.split('_')[-1]}."
                }
                for vector_id in vector_id_list
            }
            return DummyFetchResponse(namespace, vectors)

        self.mock_pinecone_client.fetch_by_vector_ids = MagicMock(side_effect=mock_fetch_by_vector_ids)

        # Call the function under test
        fetch_result = fetch_complete_doc_text(matches, self.mock_pinecone_client)

        # Expected output: Combined text for each document ID
        expected_output = {
            "job123": "This is chunk 1. This is chunk 2.",
            "job456": "This is chunk 1. This is chunk 2."
        }

        # Assertions
        self.assertEqual(fetch_result, expected_output)
        self.mock_pinecone_client.fetch_by_vector_ids.assert_called()


    @patch("graph.nodes.process_retrieved_docs")
    @patch("graph.nodes.format_context_for_llm")
    def test_augmentation_node(self, mock_format_context, mock_process_docs):
        """Test augmentation_node updates final_context correctly."""

        # Mock the processed docs
        mock_process_docs.return_value = {
            "abc123": {
                "score": 0.95,
                "url": "https://example.com/job/abc123",
                "combined_raw_text": "AI is evolving."
            }
        }

        # Mock the formatted context
        mock_format_context.return_value = "[Metadata] Source: https://example.com/job/abc123, Relevance: 0.95\n[Content] AI is evolving."

        result = augmentation_node(self.state, self.mock_pinecone_client)

        self.assertIn("final_context", result)
        self.assertIsInstance(result["final_context"], str)
        self.assertNotEqual(result["final_context"], "")  # Ensure context is not empty

        # Verify mocks were called
        mock_process_docs.assert_called_once_with(self.state["retrieved_docs"], self.mock_pinecone_client)
        mock_format_context.assert_called_once_with(mock_process_docs.return_value, self.mock_settings.pinecone.max_docs)

    
    @patch("graph.nodes.fetch_complete_doc_text")
    def test_process_retrieved_docs(self, mock_fetch_complete_doc_text):
        # Mock response for fetch_complete_doc_text
        mock_fetch_complete_doc_text.return_value = {
            "job123": "This is chunk one. This is chunk two.",
            "job456": "This is chunk one. This is chunk two."
        }

        # Mock matches input
        matches = [
            {
                "id": "job123_chunk_1",
                "score": 0.92,
                "metadata": {
                    "firestoreId": "job123",
                    "docType": "job",
                    "chunk": 1,
                    "total_chunks": 2,
                    "raw_data": "This is chunk one."
                }
            },
            {
                "id": "job456_chunk_2",
                "score": 0.85,
                "metadata": {
                    "firestoreId": "job456",
                    "docType": "job",
                    "chunk": 2,
                    "total_chunks": 2,
                    "raw_data": "This is chunk two."
                }
            }
        ]
        # Call the function
        result = process_retrieved_docs(matches, None)  # No need for PineconeClient here

        # Expected output
        expected_output = {
            "job123": {
                "score": 0.92,
                "combined_raw_text": "This is chunk one. This is chunk two.",
                "url": "https://example.com/jobs/job123"
            },
            "job456": {
                "score": 0.85,
                "combined_raw_text": "This is chunk one. This is chunk two.",
                "url": "https://example.com/jobs/job456"
            }
        }

        # Validate output
        self.assertEqual(result["job123"]["score"], expected_output["job123"]["score"])
        self.assertEqual(result["job123"]["combined_raw_text"], expected_output["job123"]["combined_raw_text"])
        self.assertEqual(result["job123"]["url"], expected_output["job123"]["url"])
        self.assertEqual(result["job456"]["score"], expected_output["job456"]["score"])
        self.assertEqual(result["job456"]["combined_raw_text"], expected_output["job456"]["combined_raw_text"])
        self.assertEqual(result["job456"]["url"], expected_output["job456"]["url"])

    def test_format_context_for_llm(self):
        """Test formatting processed documents into context for LLM."""
        processed_docs = { 
            "job123": {
                "score": 0.92,
                "combined_raw_text": "This is chunk one. This is chunk two.",
                "url": "https://example.com/jobs/job123"
            },
            "job456": {
                "score": 0.85,
                "combined_raw_text": "This is chunk one. This is chunk two.",
                "url": "https://example.com/jobs/job456"
            }
        }

        expected_output = (
            "[Metadata] Source: https://example.com/jobs/job123, Relevance: 0.92\n"
            "[Content] This is chunk one. This is chunk two.\n\n"
            "[Metadata] Source: https://example.com/jobs/job456, Relevance: 0.85\n"
            "[Content] This is chunk one. This is chunk two.\n"
        )

        result = format_context_for_llm(processed_docs)
        self.assertEqual(result.strip(), expected_output.strip())

    def test_format_context_for_llm_with_limit(self):
        """Test formatting processed documents into context for LLM."""
        processed_docs = { 
            "job123": {
                "score": 0.92,
                "combined_raw_text": "This is chunk one. This is chunk two.",
                "url": "https://example.com/jobs/job123"
            },
            "job456": {
                "score": 0.85,
                "combined_raw_text": "This is chunk one. This is chunk two.",
                "url": "https://example.com/jobs/job456"
            }
        }

        expected_output = (
            "[Metadata] Source: https://example.com/jobs/job123, Relevance: 0.92\n"
            "[Content] This is chunk one. This is chunk two.\n\n"
        )

        result = format_context_for_llm(processed_docs, 1)
        self.assertEqual(result.strip(), expected_output.strip())

    def test_final_response_node(self):
        
        self.mock_chain.invoke.return_value.content = "AI is the simulation of human intelligence in machines."
        """Test final_response_node correctly invokes chain and updates state."""
        result = final_response_node(self.state, self.mock_chain)

        # Check if response is correctly stored in result
        expected_response = "AI is the simulation of human intelligence in machines."
        self.assertEqual(result["response"], expected_response)

        # Ensure response is appended to state messages
        self.assertEqual(len(self.state["messages"]), 3)  # 2 existing + 1 new message
        self.assertEqual(self.state["messages"][-1].content, expected_response)

        # Ensure chain.invoke was called with the correct inputs
        self.mock_chain.invoke.assert_called_once_with({
            "context": self.state["final_context"],
            "input": self.state["query"]
        })


if __name__ == "__main__":
    unittest.main()