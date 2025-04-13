from typing import Optional, Any, List, Tuple, Dict
from ragas.testset.persona import Persona
import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.testset.synthesizers import default_query_distribution
from langchain_core.documents import Document
from ragas.testset import TestsetGenerator
import pandas as pd
from settings import logger


class RAGASQueryGenerator:
    """
    A class to generate test queries based on documents using RAGAS and LLM models.
    
    This generator uses the RAGAS framework to create realistic test queries from a set
    of documents. It leverages personas to create role-specific queries and can be
    configured with different query distribution patterns to simulate various user
    behaviors and query complexities.
    """

    def __init__(self, genimi_api_key: Optional[str] = None, llm:Any = None, embeddings:Any = None):
        """
        Initialize the RAGAS Query Generator.
        
        Args:
            genimi_api_key: Google Generative AI API key (defaults to environment variable)
            llm: Optional custom LLM model (uses Gemini by default)
            embeddings: Optional custom embedding model (uses Gemini embeddings by default)
            
        Raises:
            ValueError: If Gemini API key is not provided and not in environment variables
        """
        self._genimi_api_key = genimi_api_key or os.environ.get("GEMINI_API_KEY")
        if not self._genimi_api_key:
            raise ValueError("Gemini API key is required. Provide as parameter or set GEMINI_API_KEY environment variable.")
        
        self._default_model = "gemini-2.0-flash-001"
        self._default_embedding = "models/text-embedding-004"
        self._llm = llm
        self._embeddings = embeddings
        self._evaluator_llm = None
        self._embedding_ragas = None
        self._generator = None
        self._personas = None  # Will be initialized when needed
        self._query_distribution = None
        
        self._initialize_models()
        logger.info("RAGAS Query Generator initialization complete")

    def _initialize_models(self):
        """
        Initialize the LLM and embedding models.
        
        This method sets up the language model and embedding model needed for RAGAS,
        either using the provided models or creating new ones with the default configuration.
        
        Raises:
            Exception: If there's an error during model initialization
        """

        try:
            if not self._llm:
                logger.info(f"Creating Default LLM instance with model: {self._default_model}")
                self._llm = ChatGoogleGenerativeAI(
                    api_key=self._genimi_api_key, 
                    model=self._default_model
                )
            else:
                logger.info(f"Using custom provided LLM model: {self._llm}")
            
            if not self._embeddings:
                logger.info(f"Creating default embeddings instance with model: {self._default_embedding}")
                self._embeddings = GoogleGenerativeAIEmbeddings(
                    google_api_key=self._genimi_api_key, 
                    model=self._default_embedding
                )
            else:
                logger.info(f"Using custom provided embeddings model: {self._embeddings}")

            logger.info("Creating RAGAS compatible wrappers for models")
            self._evaluator_llm = LangchainLLMWrapper(self._llm)
            self._embedding_ragas = LangchainEmbeddingsWrapper(self._embeddings)

            logger.info("LLM and embedding models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    def _create_default_query_distribution(self) -> List[Tuple]:
        """
        Create default query distribution for query generation.
        
        This sets up the distribution of query types:
        - Simple queries (65%): Straightforward questions about single facts
        - Complex queries (25%): Questions requiring synthesis of multiple facts
        - Multi-hop queries (10%): Questions requiring multiple reasoning steps
        
        Returns:
            List of tuples containing query types and their distribution weights
        """
        base_dist = default_query_distribution(llm=self._evaluator_llm)
        query_dist_modified = [
            (base_dist[0][0], 0.65),
            (base_dist[1][0], 0.25),
            (base_dist[2][0], 0.10)
        ]
        logger.info(f"Using Default query distribution.")
        return query_dist_modified

    def _create_default_personas(self) -> List[Persona]:
        """
        Create default personas for query generation.
        
        These personas represent different user profiles with specific information needs:
        - Active Job Seeker: Looking for jobs matching their skills
        - Interview Preparation Researcher: Preparing for interviews
        - Career Transition Explorer: Researching career changes
        
        Returns:
            List of Persona objects
        """
        logger.info("Creating default personas for query generation")
        return [
            Persona(
                name="Active Job Seeker",
                role_description="You are a professional actively searching for new job opportunities. You want to find relevant job postings that match your skillset and experience level. You're interested in understanding job requirements, salary ranges, company culture, and application processes. Ask specific questions about job listings, recruiter posts, salary, benefits and how to determine if a position would be a good fit for your background."
            ),
            
            Persona(
                name="Interview Preparation Researcher",
                role_description="You are a job candidate preparing for upcoming interviews. You're looking for real interview experiences from people who interviewed for positions you're targeting. You want to understand common interview questions, assessment formats, and how to prepare effectively. Ask questions about specific interview processes, what helped others succeed, and preparation strategies for roles you're considering."
            ),
            
            Persona(
                name="Career Transition Explorer",
                role_description="You are a professional considering a career change into a new field. You're researching what skills you need to develop, what entry-level positions to target, and how others have successfully made similar transitions. Ask questions about skill development, education requirements, and strategies for breaking into industries that are new to you."
            )
        ]

    def generate_queries(self, docs: List[Document],
                         testset_size: int = 10, 
                         query_distribution: Optional[List[Tuple]] = None,
                         personas: Optional[List[Persona]] = None) -> pd.DataFrame:
        """
        Generate test queries from documents.
        
        This is the main method that generates test queries using the RAGAS framework.
        It creates questions that simulate real user queries based on the provided documents,
        using the configured personas and query distribution.
        
        Args:
            docs: List of Langchain Document objects to generate queries from
            testset_size: Number of queries to generate (default: 10)
            query_distribution: Optional custom query distribution
            personas: Optional custom List[Persona]
            
        Returns:
            DataFrame containing generated test queries
        """

        if personas:
            logger.info(f"Using provided Personas")
            self._personas = personas
        else:
            self._personas = self._create_default_personas()
            logger.info(f"No personas provided. Using default personas")

        if query_distribution:
            logger.info(f"Using provided query distribution")
            self._query_distribution = query_distribution
        else:
            logger.info(f"No query distribution provided. Using deafult query distributions")
        if not self._query_distribution:
                self._query_distribution = self._create_default_query_distribution()

        logger.info(f"Initializing RAGAS TestsetGenerator with")
        self._generator = TestsetGenerator(llm=self._evaluator_llm, 
                                           embedding_model=self._embedding_ragas, 
                                           persona_list=self._personas)
        
        logger.info(f"Generating {testset_size} test queries")
        generated_testset = self._generator.generate_with_langchain_docs(
            docs,
            testset_size=testset_size,
            query_distribution=self._query_distribution
        )
        df_testset = generated_testset.to_pandas()
        logger.info(f"Generated testset with Number of records: {len(df_testset)}")
        return df_testset

    def set_personas(self, personas: List[Persona]):
        """
        Set custom personas for query generation.
        
        This allows customizing the personas used for query generation beyond the defaults.
        Each persona represents a different user profile with specific information needs.
        
        Args:
            personas: List of Persona objects
        """
        self.personas = personas
        logger.info(f"Successfully set personas")

    def set_query_distribution(self, query_distribution: Dict[str, float]) -> None:
        """
        Set custom query distribution for generating different query types.
        
        This method allows setting a custom distribution of query types:
        - SIMPLE_QUERIES: Straightforward questions about single facts
        - MULTI_HOP_DIRECT: Questions requiring synthesis of multiple facts
        - MULTI_HOP_COMPLEX: Questions requiring multiple reasoning steps
        
        Args:
            query_distribution: Dictionary with keys SIMPLE_QUERIES, MULTI_HOP_DIRECT, 
                               and MULTI_HOP_COMPLEX, and float values representing weights
                               
        Raises:
            ValueError: If required keys are missing from the distribution
        """
        try:
            expected_keys = ["SIMPLE_QUERIES", "MULTI_HOP_DIRECT", "MULTI_HOP_COMPLEX"]
            # validate input
            for key in expected_keys:
                if key not in query_distribution:
                    raise ValueError(f"Missing key : {key}")

            base_dist = default_query_distribution(llm=self._evaluator_llm)
            self._query_distribution = [
                                            (base_dist[0][0], query_distribution["SIMPLE_QUERIES"]),  # Simple queries
                                            (base_dist[1][0], query_distribution["MULTI_HOP_DIRECT"]),  # Complex queries
                                            (base_dist[2][0], query_distribution["MULTI_HOP_COMPLEX"])   # Multi-hop queries
                                        ]
            
            
            logger.info(f"Successfully set query distribution as per : {query_distribution}")
        except Exception as e:
            logger.error(f"Failed to set query distribution. Will use default to generate if not reset. {str(e)}")