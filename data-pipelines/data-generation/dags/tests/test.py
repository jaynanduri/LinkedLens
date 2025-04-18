import sys
import os
from unittest.mock import MagicMock, patch
import uuid
import pandas as pd
import unittest
import pandas as pd
import numpy as np
import json

import pydantic_core


# Get the path to the project's root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.utils.post_gen_helper import create_company_user_map
# from src.utils.preprocessing import clean_company_ids, enrich_and_clean_postings
from src.schema.job_posting import JobPosting
from src.utils.post_gen import post_generation

class DummyPostChain:
    def invoke(self, payload):
        # Return a dummy response with a content attribute.
        class DummyResponse:
            content = f"Interview experience post for {payload['company_name']} - {payload['position_role']}"
        return DummyResponse()

class DummyUserChain:
    def invoke(self, payload):
        # Return a dummy response with a model_dump_json method.
        class DummyUserResponse:
            def model_dump_json(self):
                # Provide dummy user details.
                return json.dumps({"first_name": "John", "last_name": "Doe"})
        return DummyUserResponse()

class DummyRateLimiter:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.num_requests = 0

    def request(self):
        return self.allowed

class TestDataGeneration(unittest.TestCase):
    def setUp(self):
        # Common test data for basic cases
        self.postings_basic = pd.DataFrame({"company_id": ["123.0", "456.5", np.nan, "789"]})
        self.companies_basic = pd.DataFrame({"company_id": ["987.0", "654.5", "321", np.nan]})
        self.expected_postings_basic = pd.Series(["123", "456", "nan", "789"], name="company_id")
        self.expected_companies_basic = pd.Series(["987", "654", "321", "nan"], name="company_id")
        self.input_df = pd.DataFrame({"company_name": ["google", "google", "google", "google"
                                                       "meta"]})
        # Create dummy chains.
        self.dummy_post_chain = DummyPostChain()
        self.dummy_user_chain = DummyUserChain()
        self.user_format_instructions = "Please provide first and last name."
        self.post_format_instructions = "Please provide post content."
        # Prepare empty lists for existing IDs.
        self.user_ids = []
        self.post_ids = []
        
        self.postings_df = pd.DataFrame({
            "company_id": [1, 2, 3],
            "title": ["Software Engineer", "Data Scientist", "Product Manager"],
            "location": ["NY", "SF", "LA"]
        })
        self.companies_df = pd.DataFrame({
            "company_id": [1, 2],
            "name": ["Company A", "Company B"]
        })

    def test_load_job_posting(self):
        row = {
        "remote_allowed": float('nan'),
        "original_listed_time": 1713397508000.0,
        "listed_time": 1713397508000.0,
        "expiry": 1715989508000.0,
        }
        with self.assertRaises(pydantic_core._pydantic_core.ValidationError):
            JobPosting(**row)

    # def test_basic_conversion(self):
    #     """Test string and NaN inputs."""
    #     cleaned_postings, cleaned_companies = clean_company_ids(self.postings_basic, self.companies_basic)
    #     # Check values
    #     pd.testing.assert_series_equal(cleaned_postings["company_id"], self.expected_postings_basic)
    #     pd.testing.assert_series_equal(cleaned_companies["company_id"], self.expected_companies_basic)
    #     # Ensure dtype is string (object)
    #     self.assertEqual(cleaned_postings["company_id"].dtype, object)
    #     self.assertEqual(cleaned_companies["company_id"].dtype, object)

    # def test_numeric_input(self):
    #     """Test numeric (float/int) inputs."""
    #     postings_numeric = pd.DataFrame({"company_id": [123.0, 456.5, np.nan, 789.0]})
    #     companies_numeric = pd.DataFrame({"company_id": [987.0, 654.5, 321.0, np.nan]})
    #     cleaned_postings, cleaned_companies = clean_company_ids(postings_numeric, companies_numeric)
    #     pd.testing.assert_series_equal(cleaned_postings["company_id"], self.expected_postings_basic)
    #     pd.testing.assert_series_equal(cleaned_companies["company_id"], self.expected_companies_basic)

    # def test_mixed_input_types(self):
    #     """Test mixed types (strings, floats, integers)."""
    #     postings_mixed = pd.DataFrame({"company_id": ["123", 456.0, np.nan, 789]})
    #     companies_mixed = pd.DataFrame({"company_id": [987, "654.0", "321", np.nan]})
    #     expected_postings = pd.Series(["123", "456", "nan", "789"], name="company_id")
    #     expected_companies = pd.Series(["987", "654", "321", "nan"], name="company_id")
    #     cleaned_postings, cleaned_companies = clean_company_ids(postings_mixed, companies_mixed)
    #     pd.testing.assert_series_equal(cleaned_postings["company_id"], expected_postings)
    #     pd.testing.assert_series_equal(cleaned_companies["company_id"], expected_companies)

    # def test_nan_handling(self):
    #     """Test NaN becomes 'nan' string."""
    #     postings_nan = pd.DataFrame({"company_id": [np.nan]})
    #     companies_nan = pd.DataFrame({"company_id": [np.nan]})
    #     cleaned_postings, cleaned_companies = clean_company_ids(postings_nan, companies_nan)
    #     self.assertEqual(cleaned_postings["company_id"].iloc[0], "nan")
    #     self.assertEqual(cleaned_companies["company_id"].iloc[0], "nan")

    # def test_zero_values(self):
    #     """Test zero (edge case)."""
    #     postings_zero = pd.DataFrame({"company_id": [0.0, "0.0"]})
    #     companies_zero = pd.DataFrame({"company_id": [0, "0.0"]})
    #     expected = pd.Series(["0", "0"], name="company_id")
    #     cleaned_postings, cleaned_companies = clean_company_ids(postings_zero, companies_zero)
    #     pd.testing.assert_series_equal(cleaned_postings["company_id"], expected)
    #     pd.testing.assert_series_equal(cleaned_companies["company_id"], expected)
    
    def test_create_user_company_map(self):
        company_user_map = create_company_user_map(self.input_df, "company_name")
        self.assertEquals(company_user_map["google"], 1)
        # self.assertRaises(KeyError, company_user_map["amazon"])
        
    # def test_company_mapping(self):
    #     """Test that company names are mapped correctly and missing mappings become empty strings."""
    #     # For company_id 3, no mapping exists so company_name should be an empty string.
    #     result = enrich_and_clean_postings(self.postings_df.copy(), self.companies_df)
    #     expected_names = ["Company A", "Company B", ""]
    #     self.assertEqual(list(result["company_name"]), expected_names)

    # def test_dropna_title(self):
    #     """Test that rows with missing title are dropped."""
    #     postings_df = pd.DataFrame({
    #         "company_id": [1],
    #         "title": [None],
    #         "location": ["NY"]
    #     })
    #     companies_df = pd.DataFrame({
    #         "company_id": [1],
    #         "name": ["Company A"]
    #     })
    #     result = enrich_and_clean_postings(postings_df.copy(), companies_df)
    #     # The row should be dropped due to missing title.
    #     self.assertTrue(result.empty)

    # def test_dropna_location(self):
    #     """Test that rows with missing location are dropped."""
    #     postings_df = pd.DataFrame({
    #         "company_id": [1],
    #         "title": ["Software Engineer"],
    #         "location": [None]  # Missing location
    #     })
    #     companies_df = pd.DataFrame({
    #         "company_id": [1],
    #         "name": ["Company A"]
    #     })
    #     result = enrich_and_clean_postings(postings_df.copy(), companies_df)
    #     self.assertTrue(result.empty)

    # def test_no_dropna_for_empty_company_name(self):
    #     """
    #     Test that rows where company_id does not have a mapping (and becomes an empty string)
    #     are NOT dropped because empty string is not considered as NaN.
    #     """
    #     postings_df = pd.DataFrame({
    #         "company_id": [3],  # No company mapping available.
    #         "title": ["Software Engineer"],
    #         "location": ["NY"]
    #     })
    #     companies_df = pd.DataFrame({
    #         "company_id": [1],
    #         "name": ["Company A"]
    #     })
    #     result = enrich_and_clean_postings(postings_df.copy(), companies_df)
    #     # Even though company_name becomes an empty string, the row should be retained.
    #     self.assertFalse(result.empty)
    #     self.assertEqual(result.iloc[0]["company_name"], "")

    # def test_multiple_rows(self):
    #     """Test function behavior on a DataFrame with multiple rows, some of which should be dropped."""
    #     postings_df = pd.DataFrame({
    #         "company_id": [1, 2, 3, 4],
    #         "title": ["Title1", None, "Title3", "Title4"],
    #         "location": ["Loc1", "Loc2", None, "Loc4"]
    #     })
    #     companies_df = pd.DataFrame({
    #         "company_id": [1, 2, 4],
    #         "name": ["Company A", "Company B", "Company D"]
    #     })
    #     result = enrich_and_clean_postings(postings_df.copy(), companies_df)
        
    #     self.assertEqual(len(result), 2)
    #     self.assertEqual(list(result["company_id"]), [1, 4])
    #     self.assertEqual(list(result["company_name"]), ["Company A", "Company D"])

    def fake_uuid_sequence(self):
        # Return two predetermined UUIDs in sequence.
        uuids = [
            uuid.UUID("00000000-0000-0000-0000-000000000001"),
            uuid.UUID("00000000-0000-0000-0000-000000000002"),
            uuid.UUID("00000000-0000-0000-0000-000000000003"),
            uuid.UUID("00000000-0000-0000-0000-000000000004"),
            uuid.UUID("00000000-0000-0000-0000-000000000005"),
            uuid.UUID("00000000-0000-0000-0000-000000000006"),
            uuid.UUID("00000000-0000-0000-0000-000000000007"),
            uuid.UUID("00000000-0000-0000-0000-000000000008"),
            uuid.UUID("00000000-0000-0000-0000-000000000009"),
            uuid.UUID("00000000-0000-0000-0000-000000000010")
        ]
        for uid in uuids:
            yield uid
    
    @patch('uuid.uuid1')
    def test_successful_generation(self, mock_uuid):
        # Set up the UUID generator to yield our predetermined values.
        gen = self.fake_uuid_sequence()
        mock_uuid.side_effect = lambda: next(gen)

        # Dummy rate limiter that always allows requests.
        rate_limiter = DummyRateLimiter(allowed=True)

        # Call the function.
        post_json, user_json = post_generation(
            user_type="user",
            user_ids=self.user_ids,
            job_id = "",
            company="TestCo",
            job_title="Software Engineer",
            post_ids=self.post_ids,
            post_chain=self.dummy_post_chain,
            user_chain=self.dummy_user_chain,
            post_format_instructions=self.post_format_instructions,
            user_format_instructions=self.user_format_instructions,
            rate_limiter=rate_limiter
        )

        # Validate output is not None.
        self.assertIsNotNone(post_json)
        self.assertIsNotNone(user_json)

        # Parse JSON outputs.
        post_data = json.loads(post_json)
        user_data = json.loads(user_json)

        # Check that our predetermined UUIDs appear.
        self.assertEqual(post_data['post_id'], "00000000-0000-0000-0000-000000000002")
        self.assertEqual(post_data['author'], "00000000-0000-0000-0000-000000000001")
        self.assertIn("Software Engineer", post_data['content'])
        self.assertIn("TestCo", post_data['content'])

        self.assertEqual(user_data['first_name'], "John")
        self.assertEqual(user_data['last_name'], "Doe")
        self.assertEqual(user_data['company'], "TestCo")
        self.assertEqual(user_data['account_type'], "user")
        self.assertEqual(user_data['user_id'], "00000000-0000-0000-0000-000000000001")


    
if __name__ == "__main__":
    unittest.main()