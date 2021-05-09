# Whats In Image

_Whats In Image_ is a service that labels picture content from uploaded images and
stores recognized image labels to a database.

In addition to image labels, _Whats In Image_-service creates thumbnails from
uploaded images and draws recognition bounding boxes to the image data.

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

### 2021-05-09 Fixing unit tests

Fixing the unit tests, currently the problem is that AWS services are not mocked
and local invokes will leak to real AWS endpoints from boto3. Lambda function uses
DynamoDB, S3 and Rekognition. Both DynamoDB and S3 can be easily mocked with moto but
Rekognition needs to be mocked with writing own mock function.

S3 and DynamoDB is now mocked but still having hard time to mock the Rekognition. It
seems to be little more complicated than expected to mock the rekognition and make sure
that only the rekognition is mocked, not anything else, this needs to be continued
