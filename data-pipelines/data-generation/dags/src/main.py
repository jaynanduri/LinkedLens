# import firebase_admin
# from firebase_admin import credentials, firestore
# from firebase_admin.firestore import DELETE_FIELD
# from datetime import datetime, timezone, timedelta
# from google.cloud.firestore_v1 import FieldFilter
# import numpy as np
# import pandas as pd

# # def update_post_collection(collection, db_client):
# #     # get all docs of collection
# #     docs = db_client.collection(collection).where(filter = FieldFilter("job_id", "!=", "")).get()
# #     print(f"Number of docs fetched for {collection}: {len(docs)}")
# #     for doc in docs:
# #         doc_ref = db.collection(collection).document(doc.id)
# #         doc_dict = doc.to_dict()
# #         author_id = doc_dict.get("author")
# #         job_id = doc_dict.get("job_id")
# #         author = db_client.collection("users").document(author_id).get()
# #         author_dict = author.to_dict()
# #         author_created_at = author_dict.get("createdAt")
# #         job = db_client.collection("jobs").document(job_id).get()
# #         job_dict = job.to_dict()
# #         job_created_at = job_dict.get("createdAt")
# #         latest_createdAt = max(author_created_at, job_created_at)
# #         print(f"Latest created at: {latest_createdAt}")
# #         converted_date = datetime.fromtimestamp(latest_createdAt)
# #         print(f"Converted date: {converted_date}")
# #         start = datetime(converted_date.year, converted_date.month, converted_date.day)
# #         end = datetime(2025, 4, 1)
# #         random_seconds = np.random.randint(
# #             0, int((end - start).total_seconds())
# #         )
# #         random_date = start + timedelta(seconds=random_seconds)
# #         current_ts = int(random_date.timestamp())
# #         ttl = current_ts + 90 * 24 * 60 * 60
# #         update_data = {
# #             "timestamp": DELETE_FIELD,  # This removes the field
# #             "createdAt": current_ts,
# #             "updatedAt": current_ts,
# #             "ttl": ttl,
# #             "vectorized": False,
# #             "vectorTimestamp" : DELETE_FIELD
# #         }
# #         doc_ref.update(update_data)
# #         print(f"Updated document {doc.id}")
# #     print(f"Completed updated for {collection} collection")

# # def update_job_collection(collection, db_client):
# #     # get all docs of collection
# #     docs = db_client.collection(collection).get()
# #     print(f"Number of docs fetched for {collection}: {len(docs)}")
# #     for doc in docs:
# #         doc_ref = db.collection(collection).document(doc.id)

# #         current_ts = int(datetime.now(timezone.utc).timestamp())
# #         ttl = current_ts + 90 * 24 * 60 * 60
# #         update_data = {
# #             "timestamp": DELETE_FIELD,  # This removes the field
# #             "createdAt": current_ts,
# #             "updatedAt": current_ts,
# #             "ttl": ttl,
# #             # "vectorized": False,
# #             # "vectorTimestamp" : DELETE_FIELD
# #         }
# #         doc_ref.update(update_data)
# #         print(f"Updated document {doc.id}")
# #     print(f"Completed updated for {collection} collection")

# # def update_user_collection(collection, db_client):
# #     # get all docs of collection
# #     docs = db_client.collection(collection).get()
# #     print(f"Number of docs fetched for {collection}: {len(docs)}")
# #     for doc in docs:
# #         doc_ref = db.collection(collection).document(doc.id)
# #         start = datetime(2025, 2, 1)
# #         end = datetime(2025, 3, 21)
# #         random_seconds = np.random.randint(
# #             0, int((end - start).total_seconds())
# #         )
# #         random_date = start + timedelta(seconds=random_seconds)
# #         current_ts = int(random_date.timestamp())
# #         update_data = {
# #             # "timestamp": DELETE_FIELD,  # This removes the field
# #             "createdAt": current_ts,
# #             "updatedAt": current_ts,
# #             # "vectorized": False,
# #             # "vectorTimestamp" : DELETE_FIELD
# #         }
# #         doc_ref.update(update_data)
# #         print(f"Updated document {doc.id}")
# #     print(f"Completed updated for {collection} collection")

# # def check_missing_job_ids(db_client):
# #     jobs_docs = db_client.collection("jobs").get()
# #     job_ids = {doc.id for doc in jobs_docs}
# #     print(f"Total jobs found: {len(job_ids)}")

# #     posts = db_client.collection("posts").where(filter=FieldFilter("job_id", "!=", "")).get()
# #     print(f"Total posts with job_id: {len(posts)}")

# #     missing_job_id_post_ids = [
# #         post.id for post in posts if post.to_dict().get("job_id") not in job_ids
# #     ]
# #     print(f"Total posts with missing job references: {len(missing_job_id_post_ids)}")
# #     print(f"Posts with missing job_id references: {missing_job_id_post_ids}")


# if __name__ == '__main__':
#     try:
#         cred = credentials.Certificate('../../../credentials/linkedlens-firestore-srvc-acc.json')
#         firebase_admin.initialize_app(cred)
#         db = firestore.client(database_id='linked-lens')
#         print("DB:", db)
#         # get posts with job_ids
#         post_job_ids = []
#         post_jobs = db.collection("posts").where(filter=FieldFilter("job_id", "!=", "")).get()
#         print(f"Total posts with job_id: {len(post_jobs)}")
#         for post in post_jobs:
#             post_dict = post.to_dict()
#             post_job_ids.append(post_dict.get("job_id"))

#         print(f"Total job_ids in posts: {len(post_job_ids)}")

#         # get all job ids
#         jobs_data = []
#         for job_id in post_job_ids:
#             job = db.collection("jobs").document(job_id).get()
#             if not job.exists:
#                 print(f"Job ID {job_id} does not exist in jobs collection.")
#             else:
#                 job_dict = job.to_dict()
#                 jobs_data.append({
#                     "job_id": job_id,
#                     "company_name": job_dict.get("company_name", ""),
#                     "title": job_dict.get("title", ""),
#                     "location": job_dict.get("location", ""),
#                 })

#         df = pd.DataFrame(jobs_data)
#         df.to_csv("jobs.csv", index=False)
#         print("Job data saved to jobs.csv")
#     except Exception as e:
#         print(f"Failed: {e}")

# # """
# # Update all records
# # Users - add createdAt and UpdatedAt in int
# # Posts - Update timestamp change to createdAt to utc timezone and add UpdatedAt
# # Jobs - add createdAt and UpdatedAt in int
# # """

# # """
# # Jobs - should not have author
# # User - created_at, updated_at
# # Posts: created_at, upadted_at amd ttl - remove timestamp
# # After additinal filter to remove jobs with deadlines, check for each post with job id, if job_id not in Jobs remove
# # For new posts : update time to UTC and JOBS*****
# # Reload all jobs
# # Remove any posts if needed - check count
# # Update the created_at for all posts

# # """
# # """
# # 1. check the pydantic class for jobs
# # 2. Backup jobs
# # 3. Load jobs


# # 5. Update createdAt and updatedAt for users - pick random datetime(range)
# # 6. For all posts - remove timestamp and add created_at, updated_at, ttl
# #    - current for posts with job_id
# #    - for posts without job_id - pick random datetime(range) > creaatedAT of author.. 

# # 4. Check for posts with job ids if any need to be deleted
# # """

# # """
# # Update pydantic for User, Post and JobPostings
# # """
