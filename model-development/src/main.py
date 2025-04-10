import uvicorn
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from logger import logger
from datetime import datetime
from endpoints import router
import json
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    cleaned_errors = []
    for err in exc.errors():
        err.pop("ctx", None)  # remove context entirely
        cleaned_errors.append(err)
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"error": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error: {str(exc)}")
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": f"Internal server error: {str(exc)}"
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    # response = await call_next(request)

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Middleware caught unhandled exception: {str(e)}")
        raise
    process_time = (datetime.now() - start_time).total_seconds()
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time": process_time,
        "client_ip": request.client.host,
    }
    logger.info(json.dumps(log_data))
    return response


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)