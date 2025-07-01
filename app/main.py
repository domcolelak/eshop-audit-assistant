from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.audit import run_audit
from app.repair_assistant import navrh_na_zaklade_chyby

import csv
import io
import os
import tempfile
import shutil

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

last_audit_result = {}
last_feed_path = ""
last_feed_type = ""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Pr zdny formul r, bez v sledkov
    return templates.TemplateResponse("index.html", {
        "request": request,
        "audit": {},
        "feed_url": ""
    })

@app.post("/", response_class=HTMLResponse)
async def upload_feed(request: Request, feed_file: UploadFile = File(...)):
    global last_audit_result, last_feed_path, last_feed_type

    # Ulo  me uploadnut  s bor do temp s boru
    _, ext = os.path.splitext(feed_file.filename.lower())
    suffix = ext if ext in [".xml", ".csv"] else ".xml"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(feed_file.file, tmp)
        tmp_path = tmp.name

    result = await run_audit(tmp_path)
    last_audit_result = result
    last_feed_path = tmp_path
    last_feed_type = result.get("typ_feedu", "")

    return templates.TemplateResponse("results.html", {
        "request": request,
        "audit": result,
        "feed_url": "upload"
    })

@app.post("/upload-feed", response_class=HTMLResponse)
async def upload_feed_alt(request: Request, feedfile: UploadFile = File(...)):
    global last_audit_result, last_feed_path, last_feed_type

    _, ext = os.path.splitext(feedfile.filename.lower())
    suffix = ext if ext in [".xml", ".csv"] else ".xml"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(feedfile.file, tmp)
        tmp_path = tmp.name

    result = await run_audit(tmp_path)
    last_audit_result = result
    last_feed_path = tmp_path
    last_feed_type = result.get("typ_feedu", "")

    return templates.TemplateResponse("results.html", {
        "request": request,
        "audit": result,
        "feed_url": "upload"
    })

@app.get("/results", response_class=HTMLResponse)
async def view_results(request: Request):
    return templates.TemplateResponse("results.html", {
        "request": request,
        "audit": last_audit_result,
        "feed_url": last_feed_path
    })

@app.get("/shoptet", response_class=HTMLResponse)
async def shoptet_admin(request: Request, feed_url: str = ""):
    vysledky = {}
    if feed_url:
        vysledky = await run_audit(feed_url)
    return templates.TemplateResponse("shoptet_admin.html", {
        "request": request,
        "feed_url": feed_url,
        "vysledky": vysledky
    })

@app.get("/export")
async def export_csv():
    global last_audit_result
    output = io.StringIO(newline="")
    output.write('\ufeff')  # BOM for UTF-8

    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Typ chyby", "Hodnota"])

    for key, values in last_audit_result.items():
        if key == "typ_feedu":
            continue
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict):
                    writer.writerow([key, f"{item.get('id', '')} - {item.get('nazov', '')}"])
                else:
                    writer.writerow([key, item])
        else:
            writer.writerow([key, values])

    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=audit.csv"
    })

@app.get("/navrhy-oprav", response_class=HTMLResponse)
async def repair_suggestions(request: Request):
    global last_feed_type

    navrhy = {}

    for kategoria, produkty in last_audit_result.items():
        if kategoria == "typ_feedu":
            continue
        if isinstance(produkty, list) and produkty:
            vysledky = []
            for produkt in produkty:
                if isinstance(produkt, dict):
                    oprava = navrh_na_zaklade_chyby(kategoria, produkt, typ_feedu=last_feed_type)
                    vysledky.append({
                        "id": produkt.get("id", ""),
                        "nazov": produkt.get("nazov", ""),
                        "navrh": oprava
                    })
            if vysledky:
                navrhy[kategoria] = vysledky

    return templates.TemplateResponse("repair_suggestions.html", {
        "request": request,
        "navrhy": navrhy
    })
