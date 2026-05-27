# floci Bootstrap Plan

Phase 1 keeps floci as an explicit integration boundary because local install commands vary by workstation.

Expected resources:

- S3-compatible bucket: `inferhub-model-artifacts`
- ECR-compatible repositories: `inferhub/gateway`, `inferhub/llm-worker`, `inferhub/asr-worker`, `inferhub/tts-worker`, `inferhub/vision-worker`
- IAM-compatible access key for local development

Example boto3 pattern for later phases:

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url=settings.floci_endpoint_url,
    region_name=settings.floci_region,
    aws_access_key_id=settings.floci_access_key_id,
    aws_secret_access_key=settings.floci_secret_access_key,
)
```

