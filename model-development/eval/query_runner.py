from typing import Optional
import pandas as pd
from langgraph.graph.state import CompiledStateGraph
import os
import sys
from typing import List, Dict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from settings import logger
from datetime import datetime
from endpoints import clapp, create_default_state
from langchain_core.messages import HumanMessage

class QueryGraphRunner:
    """
    Runner for executing test queries through a LangGraph workflow.
    
    This class initialises graph from the endpoints module to run
    a set of test queries. It's designed for testing and evaluating the performance
    of LLM-based conversation systems by running queries in batch mode and tracking
    their results in LangSmith.
    """
    def __init__(self, testset_df: pd.DataFrame, run_env: str = "test"):
        """
        Initialize the Query Graph Runner with a testset DataFrame.
        
        Args:
            testset_df: DataFrame containing test queries to run
            run_env: Environment for running the graph (e.g., "test", "prod")
            
        Raises:
            ValueError: If the graph cannot be initialized
        """
        logger.info("Initializing QueryGraphRunner", extra={"json_fields": {
            "run_env": run_env,
            "testset_size": len(testset_df)
        }})
        # Reuse the existing graph from endpoints
        self.graph = clapp.graph
        self.run_env = run_env
        self.testset = testset_df
        if not self.graph:
            logger.error(f"Error initializing graph: {str(e)}")
            raise ValueError(f"Failed to initialise graph..")
        logger.info(f"QueryGraphRunner initialized with {len(testset_df)} test queries in '{run_env}' environment")

    def get_testdata(self) -> pd.DataFrame:
        """
        Get the testset DataFrame.
        
        Returns:
            The DataFrame containing test queries
        """
        return self.testset
    
    def run_queries(self, df: Optional[pd.DataFrame] = None, query_column: str = "user_input"):
        """
        Execute queries from a DataFrame through the graph.
        
        This method iterates through rows in the provided DataFrame (or the default testset),
        sending each query through the graph. Results are logged to LangSmith for further 
        analysis and progress is reported in the application logs.
        
        Args:
            df: Optional DataFrame containing queries to run. If None, uses self.testset
            query_column: Column name in DataFrame containing query strings (default: "user_input")
            
        Returns:
            None: Results are logged to LangSmith instead of being returned
            
        Raises:
            ValueError: If no DataFrame is available (neither provided nor in self.testset)"
        """

        if not self.graph:
            logger.warning("Graph is not initialized or available")
            return
        
        df_to_use = df if df is not None else self.testset
        if df_to_use is None or df_to_use.empty:
            raise ValueError("No DataFrame available for query execution. "
                            "Either provide a DataFrame or initialize with a valid testset.")
        if query_column not in df_to_use.columns:
            logger.error(f"Column '{query_column}' not found in DataFrame")
            return
        
        total = len(df_to_use)
        logger.info(f"Executing {total} queries using column '{query_column}'")
        completed = 0
        errors = 0

        for idx, row in df_to_use.iterrows():
            query = row[query_column]

            config = {"configurable": {
                            "thread_id": f"{idx}_{str(datetime.now())}", 
                            "user_id": idx, 
                            "chat_id": idx,
                            "run_env": self.run_env
                        }
            }

            try:
                # Create and populate state
                state = create_default_state()
                state["query"] = query
                state["messages"].append(HumanMessage(content=query))

                result_state = self.graph.invoke(state, config)

                logger.info(f"Executed query {idx}: '{query}'")
                if result_state.get("messages") and len(result_state["messages"]) > 1:
                    logger.info(f"Response length: {len(result_state['messages'][-1].content)} characters")
                completed += 1
                
            except Exception as e:
                logger.error(f"Error executing query {idx} '{query}': {e}")
                errors += 1

            if completed % 5 == 0 or completed == total:
                logger.info(f"Progress: {completed}/{total} queries completed ({errors} errors)",
                            extra={"json_fields": {"completed": completed, "total": total, "errors": errors}})

        return