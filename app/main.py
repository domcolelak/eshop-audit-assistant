from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.audit import run_audit
from app.repair_assistant import navrh_na_zaklade_chyby

import csv
import io
import os
import tempfile
import shutil
import traceback
from openai import OpenAI
from dotenv import load_dotenv

# Načítaj .env súbor do prostredia
load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

last_audit_result = {}
last_feed_path = ""
last_feed_type = ""

# Inicializuj OpenAI klienta
client = OpenAI()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Return empty form, no results
    return templates.TemplateResponse("index.html", {
        "request": request,
        "audit": {},
        "feed_url": ""
    })

@app.post("/", response_class=HTMLResponse)
async def upload_feed(request: Request, feed_file: UploadFile = File(...)):
    global last_audit_result, last_feed_path, last_feed_type

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

@app.post("/api/generate-repair")
async def generate_repair(kategoria: str = Form(...), produkt_id: str = Form(...), nazov: str = Form(...)):
    if not os.getenv("OPENAI_API_KEY"):
        return JSONResponse(status_code=500, content={"error": "OpenAI API key not configured"})

    prompt = (
        f"Produkt ID: {produkt_id}\n"
        f"Názov produktu: {nazov}\n"
        f"Kategória chyby: {kategoria}\n\n"
        "Navrhni stručný a jasný návrh opravy tejto chyby v produktovom feede e-shopu."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )
        navrh = response.choices[0].message.content.strip()
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"OpenAI API error: {str(e)}"})

    return {"navrh": navrh}
