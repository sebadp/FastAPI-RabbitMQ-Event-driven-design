from fastapi import FastAPI

from app.routers import orders, products
from app.models.database import engine, Base

app = FastAPI()

# Run database migration on startup
Base.metadata.create_all(bind=engine)

app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(products.router, prefix="/api", tags=["Products"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Bienvenido a Real-Time Order Processing 🚀"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
