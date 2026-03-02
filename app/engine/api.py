from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as main_router

app = FastAPI(title="QuantLux API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix="/api/v1")
