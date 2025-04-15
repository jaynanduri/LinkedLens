# Data Exploration & Bias Detection

This section presents some exploratory data analysis (EDA) performed on the Kaggle dataset used in LinkedLens, with a focus on identifying potential biases through data slicing and visualizations.

## Data Bias Detection Using Data Slicing

Since the dataset from Kaggle is not representative of the entire job market, we need to be aware of potential biases in the data. Below are some interesting slices of the data that can help us understand the biases:

![top-30-job-titles.png](/images/top-30-job-titles.png)
The dataset is skewed towards software engineering roles, with the top job titles being related to software development.

![top-40-companies.png](/images/top-40-companies.png)
The dataset contains job postings from a variety of companies, with the top companies being well-known tech giants, however usual suspects like Apple, Meta/Facebook are missing. The distribution of companies is definitely not representative of the entire job market.

![top-industries.png](/images/top-industries.png)
The industries are definitely dominated by tech companies, with the top industries being related to technology and software development.
