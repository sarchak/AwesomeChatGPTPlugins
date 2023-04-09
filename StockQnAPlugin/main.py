import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yfinance as yf

app = FastAPI()
# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
watchlist = set()

class Stock(BaseModel):
    symbol: str


@app.get("/stock/{symbol}", tags=["stocks"])
async def get_stock_price(symbol: str):
    stock = yf.Ticker(symbol)
    historical_data = stock.history(period="1d")

    if historical_data.empty:
        raise HTTPException(status_code=404, detail="Stock not found")

    closing_price = historical_data["Close"].iloc[0]
    return {"symbol": symbol, "closing_price": closing_price}


@app.post("/watchlist", tags=["watchlist"])
async def add_stock_to_watchlist(stock: Stock):
    watchlist.add(stock.symbol)
    return {"detail": f"{stock.symbol} added to watchlist"}


@app.get("/watchlist", tags=["watchlist"])
async def get_watchlist():
    return {"watchlist": list(watchlist)}


@app.delete("/watchlist", tags=["watchlist"])
async def delete_stock_from_watchlist(stock: Stock):
    if stock.symbol not in watchlist:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")

    watchlist.remove(stock.symbol)
    return {"detail": f"{stock.symbol} removed from watchlist"}


@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def serve_manifest():
    manifest_file = os.path.join(os.path.dirname(__file__), "manifest.json")
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    return JSONResponse(content=manifest)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Stock Watchlist API",
        version="1.0.0",
        description="This is a simple API to get stock prices and manage a watchlist using FastAPI and Yahoo Finance.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

