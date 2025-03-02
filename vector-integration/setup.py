"""
Setup script for the LinkedLens Vector Integration.
"""

from setuptools import setup, find_packages

setup(
    name="linkedlens-vector-integration",
    version="1.0.0",
    description="Integration between Firestore and Pinecone Vector DB for LinkedLens",
    author="LinkedLens Team",
    packages=find_packages(),
    install_requires=[
        "pinecone>=6.0.0",
        "firebase-admin>=6.2.0",
        "sentence-transformers>=2.2.2",
        "python-dotenv>=1.0.0",
        "pydantic>=2.4.2",
        "loguru>=0.7.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "linkedlens=src.main:main",
        ],
    },
    python_requires=">=3.8",
)