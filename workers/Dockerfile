FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/generated

WORKDIR /app

COPY workers/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY proto /app/proto
RUN mkdir -p /app/generated && \
    python -m grpc_tools.protoc \
      -I /app/proto \
      --python_out=/app/generated \
      --grpc_python_out=/app/generated \
      /app/proto/inferhub/v1/inference.proto

COPY workers /app/workers

EXPOSE 50051 8090

CMD ["python", "-m", "workers.common.runner"]

