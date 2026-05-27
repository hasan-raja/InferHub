import grpc
from fastapi import HTTPException, status


def grpc_error_to_http(exc: grpc.aio.AioRpcError) -> HTTPException:
    match exc.code():
        case grpc.StatusCode.INVALID_ARGUMENT:
            http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        case grpc.StatusCode.DEADLINE_EXCEEDED:
            http_status = status.HTTP_504_GATEWAY_TIMEOUT
        case grpc.StatusCode.UNAVAILABLE:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        case _:
            http_status = status.HTTP_502_BAD_GATEWAY
    return HTTPException(
        status_code=http_status,
        detail={
            "error": "worker_error",
            "grpc_status": exc.code().name,
            "message": exc.details() or "worker request failed",
        },
    )

