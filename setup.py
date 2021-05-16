import setuptools

with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="whats_in_image",
    version="0.0.1",
    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="author",
    package_dir={"": "whats_in_image"},
    packages=setuptools.find_packages(where="whats_in_image"),
    install_requires=[
        "aws-cdk.core==1.103.0",
        "aws-cdk.aws_dynamodb==1.103.0",
        "aws-cdk.aws_iam==1.103.0",
        "aws-cdk.aws_lambda_event_sources==1.103.0",
        "aws-cdk.aws_lambda_python==1.103.0",
        "aws-cdk.aws_lambda==1.103.0",
        "aws-cdk.aws_s3_notifications==1.103.0",
        "aws-cdk.aws_s3==1.103.0",
        "aws-cdk.aws_sns_subscriptions==1.103.0",
        "aws-cdk.aws_sns==1.103.0",
        "aws-cdk.aws_sqs==1.103.0",
        "aws-cdk.aws_stepfunctions==1.103.0",
        "aws-cdk.aws_stepfunctions_tasks==1.103.0",
        "moto==2.0.5",
        "black==20.8b1",
        "boto3==1.17.58",
        "flake8==3.9.2",
        "mypy==0.812",
        "pytest==6.2.3",
        "aws-lambda-powertools==1.15.0",
        "ulid-py==1.1.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
