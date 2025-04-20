import os
from datetime import datetime, timedelta, timezone
from typing import Tuple, List
from langsmith import Client
import pandas as pd
from settings import logger

class LangsmithTraceExtractor:
    """
    Extracts and processes trace data from LangSmith for evaluation purposes.
    
    This class handles the extraction of conversation traces from LangSmith, including
    queries, responses, retrieval contexts, and messages history. It processes the 
    raw data into a structured DataFrame suitable for evaluation with RAGAS and other 
    metrics.
    """
    def __init__(self, project_name: str, run_env: str, api_key: str):
        """
        Initialize the LangsmithTraceExtractor.
        
        Args:
            project_name: The name of the LangSmith project to extract traces from
            run_env: The environment ("prod" or "test") to extract traces for
            api_key: LangSmith API key for authentication
        """
        logger.info("Initializing LangsmithTraceExtractor", 
                   extra={"json_fields": {"project": project_name, "env": run_env}})
        self.project_name = project_name
        self.run_env = run_env
        logger.info("Calculating time cutoffs for trace extraction")
        self.start_cutoff, self.end_cutoff = self._calculate_cutoffs()
        logger.info("Time window for extraction", 
                   extra={"json_fields": {"start": str(self.start_cutoff), "end": str(self.end_cutoff)}})
        logger.info("Initializing Langsmith client")
        self.client = Client(api_key=api_key)
        logger.info("LangsmithTraceExtractor initialization complete")
        
        
    def _set_cutoffs_prod(self)->Tuple[datetime, datetime]:
        """
        Set time cutoffs for production environment.
        
        For production, extracts data from the previous day (1am to 1am UTC).
        
        Returns:
            Tuple of (start_cutoff, end_cutoff) datetime objects with timezone info removed
        """
        logger.info("Calculating production cutoffs")
        now_utc = datetime.now(timezone.utc)
        one_am_today_utc = now_utc.replace(hour=1, minute=0, second=0, microsecond=0).replace(tzinfo=None)
        start_cut_off, end_cut_off = one_am_today_utc - timedelta(days=1), one_am_today_utc - timedelta(minutes=1)
        logger.info(f"Standard production cutoffs: {(start_cut_off)} to {end_cut_off}")
        print(f"Expected: Start cutoff: {start_cut_off}, End cutoff: {end_cut_off}")
        # for test
        # end_cut_off = datetime(2025, 4, 11, 2, 0, 0, tzinfo=timezone.utc)
        # end_cut_off = end_cut_off.replace(tzinfo=None)
        # start_cut_off = datetime(2025, 4, 11, 1, 0, 0, tzinfo=timezone.utc)
        # start_cut_off = start_cut_off.replace(tzinfo=None)
        return start_cut_off, end_cut_off
    
    def _set_cutoffs_test(self)->Tuple:
        """
        Set time cutoffs for test environment.
        
        For test environment, starts from current time and end time
        will be set later with set_test_end_cut_off() method or during extraction.
        
        Returns:
            Tuple of (start_cutoff, None) with timezone info removed
        """
        logger.info("Calculating test environment cutoffs")
        now_utc = datetime.now(tz=timezone.utc)
        start_cut_off = datetime(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
        logger.info(f"End Time set before extracting or can be set using set_test_end_cut_off()")
        return start_cut_off, None


    def _calculate_cutoffs(self)->Tuple:
        """
        Calculate appropriate time cutoffs based on the environment.
        
        Dispatches to the appropriate method based on run_env value.
        
        Returns:
            Tuple of (start_cutoff, end_cutoff) datetime objects
            
        Raises:
            ValueError: If run_env is not 'prod' or 'test'
        """
        logger.info(f"Calculating cutoffs for environment: {self.run_env}")
        if self.run_env == "prod":
            return self._set_cutoffs_prod()
        elif self.run_env == "test":
            return self._set_cutoffs_test()
        else:
            logger.error(f"Invalid run_env value: {self.run_env}")
            raise ValueError(f"Expected run_env are prod or test")
        

    def _cleanup_retrieved_chunks(self, retrieved_chunks)->List[str]:
        """
        Extract raw text content from retrieved document chunks.
        
        Extracts and returns only the raw_data from the metadata of each
        retrieved document chunk.
        
        Args:
            retrieved_chunks: List of document chunk objects from LangSmith
            
        Returns:
            List of extracted text strings from chunks
        """
        return [
            doc.get("metadata", {}).get("raw_data", "")
            for doc in retrieved_chunks or []
            if doc.get("metadata", {}).get("raw_data", "")
        ]

    def _extract_messages_context(self, messages)->List[str]:
        """
        Extract context from conversation messages history.
        
        Creates a list of formatted message strings from the most recent messages,
        prefixed with 'User:' or 'Assistant:' based on the message type.
        
        Args:
            messages: List of message objects from the conversation history
            
        Returns:
            List of formatted message strings
        """
        context = []
        for msg in messages[-6:]:
            prefix = "User" if msg.get("type") == "human" else "Assistant"
            context.append(f"{prefix}: {msg.get('content')}")
        return context

    def set_test_end_cut_off(self):
        """
        Set the end cutoff time for test environment.
        
        This should be called after starting the extraction process in test mode,
        to set the upper bound of the time window to the current time plus one minute.
        """
        now_utc = datetime.now(timezone.utc)
        self.end_cutoff = datetime(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second) + timedelta(minutes=1)
        logger.info(f"End Cut Off set at : {str(self.end_cutoff)}")
        logger.info("Time window for extraction", 
                   extra={"json_fields": {"start": str(self.start_cutoff), "end": str(self.end_cutoff)}})

    def extract_trace_as_dataframe(self) -> pd.DataFrame:
        """
        Extract LangSmith traces and convert to a pandas DataFrame.
        
        This method:
        1. Sets the end cutoff for test environment if not already set
        2. Queries LangSmith for runs matching the project, run_env and time window
        3. Processes each run to extract relevant data
        4. Combines the data into a structured DataFrame
        
        Returns:
            DataFrame containing processed trace data
        """
        logger.info("Starting trace extraction from Langsmith")
        if not self.end_cutoff:
            self.set_test_end_cut_off()
        filter_value = (
            f'and(and(eq(metadata_key, run_env), eq(metadata_value, {self.run_env})), '
            f'and(gte(start_time, "{self.start_cutoff}"), lt(end_time, "{self.end_cutoff}")))'            
        )
        logger.info("Querying Langsmith with filter", 
                   extra={"json_fields": {"filter": filter_value}})
        runs = self.client.list_runs(project_name=self.project_name, is_root=True, filter=filter_value)
        logger.info("Processing run data")
        rows = []
        run_count = 0
        for run in runs:
            run_count += 1
            metadata = run.extra.get("metadata", {})
            if not metadata:
                logger.warning(f"No metadata found for run", 
                              extra={"json_fields": {"run_id": run.id}})
                continue
            row = {
                "run_id": run.id,
                "user_id": metadata.get("user_id"),
                "session_id": metadata.get("thread_id"),
                "chat_id": metadata.get("chat_id"),
                "start_time": run.start_time,
                "end_time": run.end_time,
                "error": run.error,
                "query": run.inputs.get("query"),
                "standalone_query": run.outputs.get("standalone_query"),
                "query_type": run.outputs.get("query_type"),
                "vector_namespace": run.outputs.get("vector_namespace"),
                "retrieved_docs": run.outputs.get("retrieved_docs"),
                "final_context": run.outputs.get("final_context"),
                "response": run.outputs.get("response"),
                "messages": run.inputs.get("messages", []),
            }
            row["messages_context"] = self._extract_messages_context(row["messages"])
            row["retrieved_context"] = self._cleanup_retrieved_chunks(row["retrieved_docs"])
            row["run_env"] = self.run_env
            rows.append(row)
            if run_count % 10 == 0:
                    logger.info(f"Processed {run_count} runs so far")
        logger.debug(f"Completed processing run {run_count}")
        
        if not rows:
            logger.warning("No valid runs found in the specified time window")
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        
        # print(df.head())
        
        logger.info("Created DataFrame from extracted data", 
                   extra={"json_fields": {"row_count": len(df), "column_count": len(df.columns)}})
        return df

