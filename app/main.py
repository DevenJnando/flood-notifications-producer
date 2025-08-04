from fastapi import FastAPI, Depends
import uvicorn
import logging

from app.routes import latest_floods, subscribers, postcodes

app: FastAPI = FastAPI()
logger = logging.getLogger("uvicorn.error")

app.include_router(subscribers.router)
app.include_router(postcodes.router)
app.include_router(latest_floods.router)

if __name__ == "__main__":
    uvicorn.run(app, log_level="info")
