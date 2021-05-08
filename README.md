# Whats In Image

_Whats In Image_ service labels picture content and persists metadata.

Images created S3 bucket will trigger pipeline where stored image is labeled with AWS
Rekognition. Acquired image labels are stored to the DynamoDB.

## Architecture

![Architecture Diagram](assets/architecture.png)
