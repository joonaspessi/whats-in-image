# Whats In Image

_Whats In Image_ is a service that labels picture content from uploaded images and
stores recognized image labels to database.

In addition to image labels, _Whats In Image_-service creates thumbnails for
uploaded images and draws recognition bounding boxes.

Todo example here

## Architecture

![Architecture Diagram](assets/architecture.png)
Images created S3 bucket will trigger pipeline where stored image is labeled with AWS
Rekognition. Acquired image labels are stored to the DynamoDB.

## Deployment

Todo how to setup the environment

## Development

Todo how to start the development

## Backlog

- [ ] unit tests
- [ ] integration tests
- [ ] region as parameter for lambda
- [ ] Step function instead of simple lamda
- [ ] Makefile
- [ ] Detect faces
- [ ] Create image thumbnail
- [ ] Bake images with rekognition bounding boxes and metadata
- [ ] Telegram bot interface
- [ ] CI/CD

## Log book

### 2021-05-10 Continue fixing unit tests

Today I will continue to setup the mock for Amazon Rekognition.
I just didn't find reasonable way of to mock the boto3 rekognition client. The need
would have been to mock this from the lambda code

```python
rekognition = boto3.client("rekognition")
```

Mocking this without touching other boto3 client became too complicated so I decided to
wrap the image labeling to a function `_detect_labels` which where internally using
Amazon Rekognition. This change made the test much more easier to mock as with this
change it is possible just to mock return value for the `_detect_labels` function which
was simple array. This could be done easily without any complex boto3 mocks, just Python
builtin unittest.mock can be used

```python
@pytest.fixture(scope="function")
def label_mock():
    with patch(
        "image_processor_lambda.image_processor_lambda._detect_labels"
    ) as mock_client:
        mock_client.return_value = {"Labels": []}
        yield
```

I think that the unit test saga is almost completed now, still have to create checks
that AWS Dynamodb contains a row and the content is reasonable.

### 2021-05-09 Fixing unit tests

Fixing the unit tests, currently the problem is that AWS services are not mocked
and local invokes will leak to real AWS endpoints from boto3. Lambda function uses
DynamoDB, S3 and Rekognition. Both DynamoDB and S3 can be easily mocked with moto but
Rekognition needs to be mocked with writing own mock function.

S3 and DynamoDB is now mocked but still having hard time to mock the Rekognition. It
seems to be little more complicated than expected to mock the rekognition and make sure
that only the rekognition is mocked, not anything else, this needs to be continued
