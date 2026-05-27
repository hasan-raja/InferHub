# floci Local Cloud

InferHub treats floci as an AWS-compatible local cloud surface.

Mapping:

- floci object storage -> S3 for model artifacts, audio uploads and trace exports
- floci registry -> ECR-style image registry for gateway and worker images
- floci credentials -> IAM-shaped local credentials
- k3d -> EKS equivalent for Kubernetes deployment phases

Configuration is intentionally AWS-shaped:

```env
FLOCI_ENDPOINT_URL=http://localhost:4566
FLOCI_REGION=us-east-1
FLOCI_ACCESS_KEY_ID=inferhub
FLOCI_SECRET_ACCESS_KEY=inferhub-local
S3_BUCKET_MODEL_ARTIFACTS=inferhub-model-artifacts
```

Python code should use boto3 clients with `endpoint_url=settings.floci_endpoint_url`.
Switching to real AWS later should only require changing endpoint and credential configuration.

