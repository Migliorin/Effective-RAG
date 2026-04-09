from core import lifespan
from fastapi import FastAPI
from routes import router_extraction


app = FastAPI(lifespan=lifespan)
app.include_router(router_extraction)