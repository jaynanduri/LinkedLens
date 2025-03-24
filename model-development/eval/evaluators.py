from evidently.future.datasets import Dataset
from evidently.future.datasets import DataDefinition
from evidently.future.datasets import Descriptor
from evidently.future.descriptors import CompletenessLLMEval, FaithfulnessLLMEval
from langsmith.schemas import Run, Example
import pandas as pd


class CompletenessEvaluator:
    def __init__(self):
        self.params = {
            "include_category": True,
            "provider": "vertex_ai",
            "model": "gemini-1.5-pro",
            "include_score": True,
        }

    def __call__(self, run: Run, example: Example | None = None) -> dict:
        try:
            df = pd.json_normalize(example.__dict__, sep="_")
            df = df[["id", "inputs_query", "outputs_context", "outputs_response"]]
            result_obj = Dataset.from_pandas(
                pd.DataFrame(df),
                data_definition=DataDefinition(
                    id_column="id", text_columns=["inputs_query", "outputs_context", "outputs_response"]
                ),
                descriptors=[CompletenessLLMEval("outputs_response", context="outputs_context", **self.params)],
            )
            result = result_obj.as_dataframe()
            res_dict = result.iloc[0].to_dict()
            return {"key": "completeness", "score": res_dict["Completeness score"]}
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            raise


class FaithfulnessEvaluator:
    def __init__(self):
        self.params = {
            "include_category": True,
            "provider": "vertex_ai",
            "model": "gemini-1.5-pro",
            "include_score": True,
        }

    def __call__(self, run: Run, example: Example | None = None) -> dict:
        try:
            df = pd.json_normalize(example.__dict__, sep="_")
            df = df[["id", "inputs_query", "outputs_context", "outputs_response"]]
            result_obj = Dataset.from_pandas(
                pd.DataFrame(df),
                data_definition=DataDefinition(
                    id_column="id", text_columns=["inputs_query", "outputs_context", "outputs_response"]
                ),
                descriptors=[FaithfulnessLLMEval("outputs_response", context="outputs_context", **self.params)],
            )
            result = result_obj.as_dataframe()
            res_dict = result.iloc[0].to_dict()
            return {"key": "faithfulness", "score": res_dict["Faithfulness score"]}
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            raise

