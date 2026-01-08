"""
Run FastAPI server with increased body size limit
This fixes the 413 Request Entity Too Large error
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        limit_concurrency=1000,
        limit_max_requests=10000,
        timeout_keep_alive=75,
        log_level="info"
    )

