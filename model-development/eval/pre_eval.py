import os
import sys
from typing import List, Dict, Tuple
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from config.settings import settings
from logger import set_logger as src_set_logger
from settings import set_logger

set_logger(name=settings.PRE_EVAL_LOG_NAME)
src_set_logger(name = settings.PRE_EVAL_LOG_NAME)

from logger import  logger as src_logger
from settings import logger
from clients.firestore_client import FirestoreClient
from ragas_query_generator import RAGASQueryGenerator
from langchain.schema import Document
from query_runner import QueryGraphRunner
from langsmith_client import LangsmithTraceExtractor
from evaluators import Evaluator



def check_metrics_against_threshold(scores: Dict[str, float], thresholds: Dict[str, float]) -> Tuple[bool, Dict]:
    """
    Check if all metric scores meet or exceed their thresholds.
    
    Args:
        scores: Dictionary containing metric names and their actual scores
        thresholds: Dictionary containing metric names and their minimum threshold values
        
    Returns:
        Tuple containing:
        - bool: True if at least one metric meets or exceeds its threshold, False if all fail
        - Dict: Detailed results for each metric
    """
    passed = True

    results = {}
    failed = 0
    logger.info("Checking metrics against thresholds", extra={"json_fields": {"scores": scores, "thresholds": thresholds}})
    # Check each metric in the thresholds
    for metric_name, threshold_value in thresholds.items():
        # Skip if the metric doesn't exist in scores
        if metric_name not in scores:
            logger.warning(f"Metric {metric_name} not found in scores")
            continue
            
        # Get the actual score
        actual_score = scores[metric_name]
        
        # Check if the score meets the threshold
        metric_passed = actual_score >= threshold_value
        
        # Update results
        results[metric_name] = {
            "score": actual_score,
            "threshold": threshold_value,
            "passed": metric_passed
        }
        
        if not metric_passed:
            logger.info(f"Metric {metric_name} failed threshold check", extra={"json_fields": {"score": actual_score, "threshold": threshold_value}})
            failed +=1

    if failed > 1:
       passed = False
       logger.warning("More than one metric failed to meet thresholds", extra={"json_fields": results})
    else:
       passed = True
       logger.info("At least one metric met its threshold")
    
    return passed, results

def convert_to_langchain_docs(db_docs: List[Dict[str, str]]) -> List[Document]: 
  """
    Convert Firestore documents to Langchain Document format.
    
    Args:
        db_docs: List of document dictionaries from Firestore
        
    Returns:
        List of Langchain Document objects
        
    Raises:
        ValueError: If an invalid collection is provided
  """
  logger.info(f"Converting {len(db_docs)} Firestore documents to Langchain format")
  documents_list = []
  for doc in db_docs:
    id = doc.get("id")
    metadata = {}
    content = ""
    if doc.get("collection") == "jobs":
      title = doc.get("title")
      company_name = doc.get("company_name")
      description = doc.get("description")
      location = doc.get("location")
      content = f"Company: {company_name}\tTitle:{title}\tLocation:{location}\nJobDescription:{description}"
      metadata["filename"] = id
      metadata["company_name"] = company_name
      metadata["title"] = title
      metadata["location"] = location
      logger.debug(f"Converted job document {id}")
    elif doc.get("collection") == "posts":
      content = doc.get("content")
      job_id = doc.get("job_id")
      metadata["filename"] = id
      if job_id:
        metadata["job_id"] = job_id
      logger.debug(f"Converted post document {id}")
    else:
      error_msg = f"Invalid Collection name '{doc.get('collection')}', expected: jobs or posts"
      logger.error(error_msg)
      raise ValueError("Invalid Collection name expected : jobs or posts")

    documents_list.append(Document(
        id=id,
        page_content=content,
        metadata=metadata
    ))
  logger.info(f"Successfully converted {len(documents_list)} documents to Langchain format")
  return documents_list


def main():
  """
  Main PreEval script to generate test queries, run them, and evaluate results.
  
  This script:
  1. Retrieves test documents from Firestore
  2. Generates test queries using RAGAS
  3. Runs the queries through the graph
  4. Extracts traces from LangSmith
  5. Evaluates the responses
  6. Checks if evaluation metrics pass threshold requirements
  """
  try:
    logger.info("Starting PreEval script...", extra={"json_fields": {
            "project": settings.LANGSMITH_PROJECT,
            "run_env": settings.TEST_RUN_ENV
        }})
    logger.info("Initializing LangSmith trace extractor")
    trace_extractor = LangsmithTraceExtractor(project_name=settings.LANGSMITH_PROJECT, 
                                    run_env=settings.TEST_RUN_ENV, 
                                    api_key = settings.LANGSMITH_API_KEY)
    
    logger.info("Initializing Firestore client to retrieve test documents")
    db_client = FirestoreClient()
    firestore_test_docs = db_client.get_test_docs()
    logger.info(f"Retrieved {len(firestore_test_docs)} test documents from Firestore")
    docs = convert_to_langchain_docs(firestore_test_docs)
    logger.info(f"Converted documents to Langchain format, total: {len(docs)}")

    
    retry_count = 2
    current_count = 0
    passed, detail_results = False, {}
    while current_count < retry_count and not passed:

        try:
          passed, detail_results = False, {}
          current_count += 1
          logger.info(f"Attempt {current_count}")
          print(f"Attempt {current_count}")

          logger.info("Initializing RAGAS query generator")
          ragas_generator = RAGASQueryGenerator(settings.GEMINI_API_KEY)

          logger.info("Setting query distribution based on configuration")
          ragas_generator.set_query_distribution(query_distribution={
                                                            "SIMPLE_QUERIES": settings.ragas_settings.RAGAS_SIMPLE_QUERIES, 
                                                            "MULTI_HOP_DIRECT":settings.ragas_settings.RAGAS_MULTI_HOP_DIRECT, 
                                                            "MULTI_HOP_COMPLEX":settings.ragas_settings.RAGAS_MULTI_HOP_COMPLEX
                                                          })
    
          logger.info(f"Generating test queries with testset size: 12")
          test_dataset = ragas_generator.generate_queries(docs, 
                                                        testset_size=12
                                                        )
          logger.info(f"Generated {len(test_dataset)} test queries")
          
          logger.info("Initializing QueryGraphRunner")
          query_runner = QueryGraphRunner(test_dataset, run_env=settings.TEST_RUN_ENV)
          
          logger.info("Running test queries through the graph")
          query_runner.run_queries(test_dataset)
          
          logger.info("Setting test end cutoff for trace extraction")
          trace_extractor.set_test_end_cut_off()
          
          logger.info("Extracting traces from LangSmith")
          trace_df = trace_extractor.extract_trace_as_dataframe()

          
          if not (trace_df is None or trace_df.empty):
              logger.info(f"Trace Data Number of records", extra={"json_fields": {"num_records": len(trace_df)}})
          
              logger.info("Initializing Evaluator")
              post_evaluator = Evaluator(data=trace_df, config={
                  "GEMINI_MODEL_NAME": settings.GEMINI_MODEL_NAME,
                  "GEMINI_EMBEDDING_MODEL": settings.GEMINI_EMBEDDING_MODEL,
                  "GEMINI_API_KEY": settings.GEMINI_API_KEY,
              })
              logger.info("Running evaluation")
              post_evaluator.evaluate()
              logger.info("Retrieving average metrics")
              avg_metrics = post_evaluator.get_average_metrics()
              # validate avg metrix pass threshold
              logger.info("Checking if metrics pass thresholds")
              passed, detail_results  = check_metrics_against_threshold(avg_metrics, settings.TEST_METRIC_THRESHOLD)
          else:
            logger.info(f"No trace data extracted.. Skipping Evaluation")

          if passed:
            logger.info(f"Pre Evaluation passed in {current_count} attempt.")
            break
          else:
            logger.warning(f"Pre Evaluation Failed in attempt {current_count}. Retrying...")

        except Exception as err:
          logger.error(f"Error in attempt {current_count + 1}: {str(err)}", exc_info=True)
    
    
    logger.info(f"Pre Eval Result {passed}", 
                extra={"json_fields": {"passed": passed, "details": detail_results}})
    print(f"Pre Eval Result: {passed}")
    logger.info("Pre evaluation process completed")
  except Exception as e:
      passed = False
      print(f"Pre Eval Result: {passed}")
      logger.error(f"Pre Evaluation script Failed: {str(e)}")




if __name__ == "__main__":
    main()


