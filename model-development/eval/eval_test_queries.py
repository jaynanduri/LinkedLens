# import os
# import sys
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
# from logger import logger
# import pandas as pd
# from langsmith.schemas import Run, Example
# from config.settings import settings
# from evaluators import *
# from graph.graph_guilder import Graph
# from graph.state import State
# from langchain.schema import HumanMessage, AIMessage
# from eval import LangSmithHandler
# from endpoints import create_default_state
# from evidently.future.datasets import Dataset
# from evidently.future.datasets import DataDefinition
# from evidently.future.datasets import Descriptor
# from evidently.future.descriptors import CompletenessLLMEval, FaithfulnessLLMEval

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from langsmith import Client, evaluate
from langsmith.schemas import Run, Example
from config.settings import settings
from graph.graph_builder import Graph
from endpoints import create_default_state
from langchain.schema import HumanMessage, AIMessage
from logger import logger
from evaluators import *
from eval import LangSmithHandler, run_evaluation
from evidently.future.datasets import Dataset
from evidently.future.datasets import DataDefinition
from evidently.future.datasets import Descriptor
from evidently.future.descriptors import CompletenessLLMEval, FaithfulnessLLMEval


class QueryGraphRunner:
    def __init__(self, csv_path: str, project_name: str, dataset_name: str, experiment_prefix: str):
        os.environ["LANGSMITH_PROJECT"] = project_name
        os.environ["LANGSMITH_DATASET"] = dataset_name
        
        self.handler = LangSmithHandler(project_name, dataset_name)
        self.queries = self.read_queries_from_csv(csv_path)
        self.graph_builder = None
        self.graph = None
        self.config = {"configurable": {"thread_id": "test_session"}}
        self.initialize_graph()
        self.experiment_prefix = experiment_prefix
    
    def read_queries_from_csv(self, csv_path):
        try:
            df = pd.read_csv(csv_path, header=None)
            return df[0].tolist()
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    def initialize_graph(self):
        try:
            self.graph_builder = Graph()
            self.graph = self.graph_builder.build_graph(isMemory=False)
        except Exception as e:
            logger.error(f"Error initializing graph: {e}")
            raise
    
    def run_queries(self):
        if not self.graph:
            logger.warning("Graph is not initialized.")
            return
        
        for query in self.queries:
            try:
                state = create_default_state()
                state["query"] = query
                state["messages"].append(HumanMessage(content=query))
                state = self.graph.invoke(state, self.config)
                logger.info(f"Executed query: {query}")
                logger.info(f"Response: {state['messages'][-1].content}")
            except Exception as e:
                logger.error(f"Error executing query '{query}': {e}")
    
    def process_runs_and_evaluate(self):
        self.handler.load_runs_into_dataset()
        run_evaluation(self.handler, self.experiment_prefix)

if __name__ == "__main__":
    CSV_PATH = "queries.csv"
    PROJECT_NAME = settings.LANGSMITH_PROJECT_NAME_TEST
    DATASET_NAME = settings.LANGSMITH_DATASET_NAME_TEST
    experiment_prefix=settings.LANGSMITH_EXPERIMENT_PREFIX_TEST
    
    runner = QueryGraphRunner(CSV_PATH, PROJECT_NAME, DATASET_NAME, experiment_prefix)
    runner.run_queries()
    runner.process_runs_and_evaluate()
