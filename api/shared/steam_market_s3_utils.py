from setuptools import setup, find_packages

setup(
    name="steam-market-s3-utils",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "botocore",
        "joblib"
    ],
    python_requires=">=3.9",
)