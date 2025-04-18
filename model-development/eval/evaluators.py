from settings import logger
from langsmith_client import LangsmithTraceExtractor
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import os
from datasets import Dataset
from ragas import evaluate
from langchain_google_genai import ChatGoogleGenerativeAI
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ragas.metrics import Faithfulness, ResponseRelevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from evidently.future.datasets import Dataset as EvidentlyDataset
from evidently.future.datasets import DataDefinition
from evidently.future.descriptors import ContextRelevance

class Evaluator:
    """
    A class for evaluating LLM responses using RAGAS and Evidently metrics.
    
    This evaluator processes trace data from LangSmith and evaluates responses based on:
    - Faithfulness: Whether the response is faithful to the context
    - Response Relevancy: Whether the response is relevant to the query
    - Retrieval Relevance: Whether the retrieved context is relevant to the query
    """
    def __init__(self, data: pd.DataFrame, config: Dict[str, Any], llm: Optional[Any] =None, embedding_model: Optional[Any] =None):
        """
        Initialize the Evaluator with data and configuration.
        
        Args:
            data: DataFrame containing 'run_id', 'query', 'response', and 'contexts' columns
            config: Configuration dictionary with API keys and model names
            llm: Optional custom LLM model (uses Gemini by default)
            embedding_model: Optional custom embedding model (uses Gemini embeddings by default)
        """
        logger.info("Initializing Evaluator", extra={"json_fields": {"records": len(data)}})
        self.data = data
        self.config = config
        if isinstance(self.data, pd.DataFrame):
            logger.info(f"Input data shape: {self.data.shape}", 
                        extra={"json_fields": {"rows": self.data.shape[0], "columns": self.data.shape[1]}})
            logger.info(f"Input columns: {', '.join(self.data.columns)}")
        
        if llm:
            logger.info("Using provided custom LLM")
            self.llm = llm
        else:
            logger.info("Using default Gemini LLM model", 
                        extra={"json_fields": {"model": self.config.get("GEMINI_MODEL_NAME")}})
            self.llm = ChatGoogleGenerativeAI(api_key=self.config.get("GEMINI_API_KEY"), model=self.config.get("GEMINI_MODEL_NAME"))
        
        if embedding_model:
            logger.info("Using provided custom embedding model")
            self.embedding_model = embedding_model
        else:
            logger.info("Using default Gemini embedding model", 
                        extra={"json_fields": {"model": self.config.get("GEMINI_EMBEDDING_MODEL")}})
            self.embedding_model = GoogleGenerativeAIEmbeddings(google_api_key=self.config.get("GEMINI_API_KEY"),
                                                                model=self.config.get("GEMINI_EMBEDDING_MODEL"))
        
        logger.info("Wrapping models for RAGAS compatibility")
        self.evaluator_llm = LangchainLLMWrapper(self.llm)
        self.embedding_ragas = LangchainEmbeddingsWrapper(self.embedding_model)
        self.text_columns = ['run_id', 'query', 'response']
        self.list_fields = ["contexts"]
        logger.info("Evaluator initialization complete")

    def _prepare_ragas_df(self)->pd.DataFrame:
        """
        Prepare the DataFrame for RAGAS evaluation.
        
        This function:
        1. Filters records to include only valid data
        2. Combines retrieved context and message context
        3. Selects and formats the required columns
        
        Returns:
            DataFrame ready for RAGAS evaluation
        """
        logger.info("Preparing DataFrame for Ragas evaluation", extra={"json_fields": {"initial_records": len(self.data)}})
        df = self.data[
            self.data["response"].notnull()
            & (self.data["retrieved_context"].notnull() | self.data["messages_context"].notnull())
            & self.data["query"].notnull()
            & self.data["error"].isnull()
        ].copy()

        logger.info("Filtered records for Ragas evaluation", extra={"json_fields": {"filtered_records": len(df)}})
        
        def combine_context_lists(row: pd.Series) -> List[str]:
            return (row.get("retrieved_context") or []) + (row.get("messages_context") or [])

        df["contexts"] = df.apply(combine_context_lists, axis=1)
        result_df = df[["run_id", "query", "contexts", "response"]]
        logger.info("Completed preparing Ragas DataFrame", extra={"json_fields": {
                                                                    "columns": result_df.columns.tolist(), 
        
                                                                "records": len(result_df)}})
        
        if len(result_df) == 0:
            logger.warning("No valid records for RAGAS evaluation after filtering!")
        elif result_df["contexts"].apply(lambda x: len(x) == 0).any():
            logger.warning("Some records have empty context lists!")
            
        return result_df

    def _convert_to_ragas_dataset(self, df: pd.DataFrame)->Dataset:
        """
        Convert a pandas DataFrame to a RAGAS Dataset format.
        
        This function:
        1. Fills null values in text columns
        2. Ensures contexts are properly formatted as lists
        3. Converts to RAGAS Dataset format
        
        Args:
            df: DataFrame prepared for RAGAS evaluation
            
        Returns:
            RAGAS Dataset object
        """
        logger.info("Converting DataFrame to Ragas Dataset", extra={"json_fields": {"records": len(df)}})
        for col in self.text_columns:
            df[col] = df[col].fillna('').astype(str)
        df['contexts'] = df['contexts'].apply(lambda x: x if isinstance(x, list) else [])
        try:
            dataset = Dataset.from_dict(df.to_dict(orient="list"))
            logger.info("Successfully converted to RAGAS Dataset")
            return dataset
        except Exception as e:
            logger.error(f"Error converting to RAGAS Dataset: {str(e)}")
            raise

    def _run_ragas_eval(self):
        """
        Run RAGAS evaluation metrics (Faithfulness and ResponseRelevancy).
        
        This function:
        1. Prepares the DataFrame for evaluation
        2. Converts to RAGAS Dataset format
        3. Runs the evaluation metrics
        4. Merges results back to the original data
        """
        logger.info("Starting Ragas evaluation: Faithfulness and Response Relevancy")
        ragas_df = self._prepare_ragas_df()

        ragas_dataset = self._convert_to_ragas_dataset(ragas_df)
        
        logger.info("Running Ragas evaluation metrics with batch size 5")
        ragas_scores = evaluate(
            dataset=ragas_dataset,
            llm=self.evaluator_llm,
            metrics=[
                Faithfulness(llm=self.evaluator_llm),
                ResponseRelevancy(llm=self.evaluator_llm, embeddings=self.embedding_ragas),
            ],
            column_map={"user_input": "query", 
                        "retrieved_contexts": "contexts"},
            batch_size=5
        )
        logger.info("RAGAS evaluation completed successfully")

        df_ragas_scores = ragas_scores.to_pandas()
        ragas_res = ragas_df.join(df_ragas_scores[["faithfulness", "answer_relevancy"]])

        logger.info("Merging Ragas scores back to original data")
        self.data["run_id"] = self.data["run_id"].astype(str).str.strip()
        ragas_res["run_id"] = ragas_res["run_id"].astype(str).str.strip()
        self.data = pd.merge(self.data, ragas_res[["run_id", "faithfulness", "answer_relevancy"]], on="run_id", how="left")
        
        logger.info("Completed merging Ragas scores", extra={"json_fields": {"scored_response_relevance": len(self.data[self.data["answer_relevancy"].notnull()]),
                                                                             "scored_faithfulness": len(self.data[self.data["faithfulness"].notnull()]),
                                                                             }})

    def _run_evidently_eval(self):
        """
        Run Evidently evaluation for context relevance.
        
        This function:
        1. Filters data for valid records
        2. Combines contexts from different sources
        3. Runs Evidently ContextRelevance evaluation
        4. Merges results back to the original data
        """

        logger.info("Starting Evidently evaluation for context relevance", extra={
            "json_fields": {
                "dataframe": len(self.data)
            }
        })

        eval_df = self.data[
            (self.data["retrieved_context"].notnull() | self.data["messages_context"].notnull())
            & self.data["response"].notnull()
            & self.data["query"].notnull()
            & self.data["error"].isnull()
        ].copy()

        logger.info("Preparing data for Evidently evaluation", extra={"json_fields": {"filtered_records": len(eval_df)}})

        logger.info("Combining contexts for Evidently evaluation")
        eval_df["contexts"] = eval_df.apply(
            lambda row: 
                (row["retrieved_context"] if isinstance(row["retrieved_context"], list) else []) + 
                (row["messages_context"] if isinstance(row["messages_context"], list) else []),
            axis=1
        )

        eval_df = eval_df[["run_id", "query", "contexts", "response"]]
        eval_df = eval_df.rename(columns={"query": "question"})

        logger.info("Running Evidently evaluations", extra={"json_fields": {"records": len(eval_df)}})

        evidently_dataset = EvidentlyDataset.from_pandas(
            eval_df,
            data_definition=DataDefinition(id_column="run_id", text_columns=["question", "contexts", "response"]),
            descriptors=[ContextRelevance("question", contexts="contexts", 
                                          output_scores=True, 
                                        #   method="llm", 
                                        #   method_params={
                                        #       "provider": "gemini",#"vertex_ai", # gemini
                                        #       "model": "gemini/gemini-1.5-flash"#self.config.get("GEMINI_MODEL_NAME"),
                                        #   },
                                           aggregation_method= "mean", alias="Relevance")]
        )
        
        logger.info("Evidently evaluation completed successfully")
        context_score_df = evidently_dataset.as_dataframe()
        logger.info("Merging Evidently scores back to original data")
        self.data["run_id"] = self.data["run_id"].astype(str).str.strip()
        context_score_df["run_id"] = context_score_df["run_id"].astype(str).str.strip()
        self.data = pd.merge(self.data, context_score_df[["run_id", "Relevance"]], on="run_id", how="left")
        logger.info("Completed Evidently evaluation", extra={"json_fields": {"scored_records": len(self.data[self.data["Relevance"].notnull()])}})

    def _log_summary(self):
        """
        Prepare and log evaluation summary.
        
        This function:
        1. Renames columns for consistency
        2. Converts data types for logging
        3. Calculates average metrics
        4. Logs individual evaluation records
        """

        logger.info("Preparing evaluation summary and logs")
        logger.info("Normalizing column names for metrics")
        self.data.rename(columns={
            "answer_relevancy": "response_relevancy",
            "Relevance": "retrieval_relevance",
            }, inplace=True)
        
        # Convert data types for logging
        self.data["start_time"] = self.data["start_time"].astype(str)
        self.data["end_time"] = self.data["end_time"].astype(str)
        self.data["error"] = self.data["error"].astype(str)

        avg_metrics = self.get_average_metrics()
        logger.info(f"Average Metrics: {avg_metrics}", extra={"json_fields": avg_metrics})

        logger.info("Logging individual evaluation records")
        for _, row in self.data.iterrows():
            row_dict = row.to_dict()
            row_dict['COMMIT_SHA'] = self.config.get("COMMIT_SHA")
            logger.info(f"Eval Entry for RunID: {row_dict['run_id']}", extra={"json_fields": row_dict})

        logger.info("Completed logging evaluation summary")
    
    def get_average_metrics(self)->Dict:
        """
        Calculate average values for evaluation metrics.
        
        Returns:
            Dictionary with average values for faithfulness, response_relevancy, 
            and retrieval_relevance
        """
        logger.info("Calculating average evaluation metrics")
        avg_metrics = self.data[["faithfulness", "response_relevancy", "retrieval_relevance"]].mean().to_dict()
        return avg_metrics

    def evaluate(self):
        """
        Run the complete evaluation process.
        
        This method orchestrates the full evaluation workflow:
        1. Run RAGAS evaluation (faithfulness and response relevancy)
        2. Run Evidently evaluation (retrieval relevance)
        3. Generate summary and logs
        
        Returns:
            The data DataFrame with evaluation metrics added
        """
        logger.info("Starting full evaluation process")
        self._run_ragas_eval()
        logger.info("Ragas evaluation completed, starting Evidently evaluation")
        self._run_evidently_eval()
        logger.info("Evidently evaluation completed, preparing summary")
        self._log_summary()
        logger.info("Evaluation process completed")