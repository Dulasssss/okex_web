import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import CHART_FILE
from data_reader import read_adds, read_candles, read_equity, read_logs, read_status, read_trades


app = FastAPI(title="OKX Paper Trading Review Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/api/status")
def api_status():
    return read_status()


@app.get("/api/trades")
def api_trades(limit: int = Query(50, ge=0, le=1000)):
    return read_trades(limit)


@app.get("/api/adds")
def api_adds(limit: int = Query(30, ge=0, le=1000)):
    return read_adds(limit)


@app.get("/api/equity")
def api_equity(limit: int = Query(500, ge=0, le=5000)):
    return read_equity(limit)


@app.get("/api/candles")
def api_candles(limit: int = Query(300, ge=0, le=5000)):
    return read_candles(limit)


@app.get("/api/logs")
def api_logs(limit: int = Query(200, ge=0, le=2000)):
    return read_logs(limit)


@app.get("/chart.png")
def chart_png():
    if not os.path.exists(CHART_FILE):
        raise HTTPException(status_code=404, detail="paper_chart.png not found")
    return FileResponse(CHART_FILE, media_type="image/png")