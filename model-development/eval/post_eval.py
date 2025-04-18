from settings import config, logger
from langsmith_client import LangsmithTraceExtractor
from evaluators import Evaluator
import pandas as pd

def main():
    """
    Main function to run the post-evaluation process.
    
    This script:
    1. Extracts conversation traces from LangSmith
    2. Evaluates the responses using RAGAS metrics
    3. Logs the evaluation results
    """
    try:
        # try adding cofing here
        logger.info("Starting post-evaluation script...", extra={
            "json_fields": {
                "run_env": config.PROD_RUN_ENV,
                "langsmith_project": config.LANGSMITH_PROJECT,
                "evaluation_models": {
                    "llm": config.GEMINI_MODEL_NAME,
                    "embeddings": config.GEMINI_EMBEDDING_MODEL
                }
            }
        })

        # Initalize Langsmith Client
        logger.info("Initializing Langsmith trace extractor", extra={"json_fields": {"project": config.LANGSMITH_PROJECT, "env": config.PROD_RUN_ENV}})
        
        trace_extractor = LangsmithTraceExtractor(project_name=config.LANGSMITH_PROJECT, 
                                    run_env=config.PROD_RUN_ENV, 
                                    api_key = config.LANGSMITH_API_KEY)
        # Extract trace data
        logger.info("Extracting trace data from Langsmith")
        trace_df = pd.DataFrame()
        trace_df = trace_extractor.extract_trace_as_dataframe()
        # check if data then eval
        if not (trace_df is None or trace_df.empty):
            logger.info(f"Trace Data Number of records", extra={"json_fields": {"num_records": len(trace_df)}})

            logger.info("Initializing evaluation pipeline")
            post_evaluator = Evaluator(data=trace_df, config={
                "GEMINI_MODEL_NAME": config.GEMINI_MODEL_NAME,
                "GEMINI_EMBEDDING_MODEL": config.GEMINI_EMBEDDING_MODEL,
                "GEMINI_API_KEY": config.GEMINI_API_KEY,
                "COMMIT_SHA": ""
            })
            logger.info("Starting evaluation process")
            post_evaluator.evaluate()
            metrics = post_evaluator.get_average_metrics()
            logger.info("Post Evaluation metrics summary", extra={"json_fields": metrics})
            
        else:
            logger.warning("No trace data found for evaluation. Check time window and filters.")
            return
        logger.info("Post-evaluation process completed")
    except Exception as e:
        logger.error(f"An error occurred during post-evaluation: {e}", extra={"json_fields": {"error": str(e)}})
    finally:
        if trace_df is not None and not trace_df.empty:
            logger.info("Cleaning up resources")
            try:
                del trace_df
                logger.info("Resources cleaned up successfully")
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {str(cleanup_error)}")

if __name__ == "__main__":
    main()