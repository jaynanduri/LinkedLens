import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from langsmith import Client, evaluate
from langsmith.schemas import Run, Example
from config.settings import settings
from logger import logger
from evaluators import *
from evidently.future.datasets import Dataset
from evidently.future.datasets import DataDefinition
from evidently.future.datasets import Descriptor
from evidently.future.descriptors import CompletenessLLMEval, FaithfulnessLLMEval

class LangSmithHandler:
    def __init__(self, project_name: str, dataset_name: str):
        self.client = Client(api_key=os.environ["LANGSMITH_API_KEY"])
        self.project_name = project_name
        self.dataset_name = dataset_name
        self.dataset = self.get_or_create_dataset()
    
    def get_or_create_dataset(self):
        try:
            dataset_list = self.client.list_datasets(dataset_name=self.dataset_name)
            for dataset in dataset_list:
                if dataset.name == self.dataset_name:
                    return dataset
            return self.client.create_dataset(
                dataset_name=self.dataset_name,
                description="Dataset created from runs containing query, final_context, and response"
            )
        except Exception as e:
            logger.error(f"Error while fetching/creating dataset: {e}")
            return None

    def get_runs(self):
        try:
            return self.client.list_runs(project_name=self.project_name, is_root=True, error=False)
        except Exception as e:
            logger.error(f"Error fetching runs: {e}")
            raise
    
    def get_existing_example_ids(self):
        try:
            example_list = self.client.list_examples(dataset_id=self.dataset.id)
            return {example.source_run_id for example in example_list}
        except Exception as e:
            logger.error(f"Error fetching existing examples: {e}")
            raise
    
    def cleanup_retrieved_chunks(self, retrieved_chunks):
        return [doc.get("metadata", {}).get("raw_data", "") for doc in retrieved_chunks if doc.get("metadata", {}).get("raw_data", "")]
    
    def load_runs_into_dataset(self):
        existing_ids = self.get_existing_example_ids()
        for run in self.get_runs():
            if run.id in existing_ids:
                logger.info(f"Run ID: {run.id} already exists in dataset. Skipping.")
                continue
            try:
                final_context = run.outputs.get("final_context", "")
                response = run.outputs.get("response", "")
                retrieved_docs_list = run.outputs.get("retrieved_docs", [])
                messages = run.outputs.get("messages", [])
                if final_context and retrieved_docs_list:
                    example = {
                        "id": run.id,
                        "inputs": {"query": run.inputs.get("query", "")},
                        "outputs": {
                            "standalone_query": run.outputs.get("standalone_query", ""),
                            "query_type": run.inputs.get("query_type", ""),
                            "vector_namespace": run.outputs.get("vector_namespace", ""),
                            "retrieved_docs": self.cleanup_retrieved_chunks(retrieved_docs_list),
                            "messages": messages,
                            "context": final_context,
                            "response": response,
                            "messages": run.outputs.get("messages", [])
                        },
                    }
                    self.client.create_example(
                        dataset_id=self.dataset.id, 
                        source_run_id=run.id, 
                        inputs=example["inputs"], 
                        outputs=example["outputs"]
                    )
                    logger.info(f"Inserted run ID: {run.id}")
            except Exception as e:
                logger.info(f"Error processing run {run.id}: {e}")

    
def run_evaluation(handler: LangSmithHandler, experiment_prefix: str):
    try:
        examples = handler.client.list_examples(dataset_id=handler.dataset.id)
        dataset_id = handler.dataset.id
        experiment_results = evaluate(
            lambda example: example,
            data=dataset_id,
            evaluators=[CompletenessEvaluator(), FaithfulnessEvaluator(), RetrievalEvaluator()],
            experiment_prefix=experiment_prefix,
            metadata={"version": "1.0.0"},
        )
        logger.info("Evaluation completed.")
    except Exception as e:
        logger.info(f"Error during evaluation: {e}")

if __name__ == "__main__":
    PROJECT_NAME = settings.LANGSMITH_PROJECT_NAME_PROD
    DATASET_NAME = settings.LANGSMITH_DATASET_NAME_PROD
    experiment_prefix=settings.LANGSMITH_EXPERIMENT_PREFIX_PROD
    
    handler = LangSmithHandler(PROJECT_NAME, DATASET_NAME)
    handler.load_runs_into_dataset()
    run_evaluation(handler, experiment_prefix)
