FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/generated

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY pytest.ini /app/pytest.ini
COPY proto /app/proto
RUN mkdir -p /app/generated && \
    python -m grpc_tools.protoc \
      -I /app/proto \
      --python_out=/app/generated \
      --grpc_python_out=/app/generated \
      /app/proto/inferhub/v1/inference.proto

COPY backend/app /app/app

EXPOSE 8080

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
