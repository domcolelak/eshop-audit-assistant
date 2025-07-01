import httpx
import xml.etree.ElementTree as ET
import re
import os
import csv
import tempfile
from collections import defaultdict
from app.detekcia import rozpoznaj_typ_feedu


def audituj_woocommerce_csv(csv_path: str) -> dict:
    result = defaultdict(list)
    result["typ_feedu"] = "woocommerce_csv"

    nazvy = defaultdict(list)
    kody = defaultdict(list)
    obrazky = defaultdict(list)

    # Inicializácia všetkých očakávaných kľúčov s prázdnymi zoznamami
    keys = [
        "produkty_bez_nazvu",
        "produkty_bez_popisu",
        "produkty_s_kratkym_popisom",
        "dlhe_nazvy",
        "dlhe_popisy",
        "popis_rovnaky_ako_nazov",
        "produkty_bez_ceny",
        "produkty_s_cenou_nula",
        "nezvycajne_nizka_cena",
        "produkty_bez_obrazka",
        "neplatna_url_obrazka",
        "obrazky_cudzia_domena",
        "obrazky_duplicita",
        "nevhodne_znaky",
        "duplicitne_nazvy",
        "duplicitne_kody",
        "produkty_bez_eanu",
        "neplatne_ean_kody",
        "nezaradene_produkty",
        "produkty_bez_vyrobcu",
    ]
    for key in keys:
        result[key] = []

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                kod = row.get("ID", "").strip() or "(bez kódu)"
                nazov = row.get("Name", "").strip()
                popis = row.get("Description", "").strip()
                cena = row.get("Regular price", "").strip()
                obrazok = row.get("Images", "").split(",")[0].strip() if row.get("Images") else ""
                ean = row.get("EAN", "").strip()
                kategoria = row.get("Categories", "").strip()
                vyrobca = row.get("Brand", "").strip()

                data = {"id": kod, "nazov": nazov}

                if not nazov:
                    result["produkty_bez_nazvu"].append(data)
                else:
                    nazvy[nazov].append(kod)
                    if len(nazov) > 70:
                        result["dlhe_nazvy"].append(data)

                if not popis:
                    result["produkty_bez_popisu"].append(data)
                else:
                    if len(popis) < 100:
                        result["produkty_s_kratkym_popisom"].append(data)
                    if len(popis) > 160:
                        result["dlhe_popisy"].append(data)
                    if nazov and nazov == popis:
                        result["popis_rovnaky_ako_nazov"].append(data)
                    if re.search(r'<[^>]+>|&[^;\s]+;', nazov + popis):
                        result["nevhodne_znaky"].append(data)

                try:
                    cena_val = float(cena)
                    if cena_val <= 0.01:
                        result["produkty_s_cenou_nula"].append(data)
                    elif cena_val < 1.0:
                        result["nezvycajne_nizka_cena"].append(data)
                except:
                    result["produkty_bez_ceny"].append(data)

                if not obrazok:
                    result["produkty_bez_obrazka"].append(data)
                else:
                    if not obrazok.startswith("http"):
                        result["neplatna_url_obrazka"].append(data)
                    if not re.search(r"(tvojeshop\.sk|myshoptet\.com|cdn\.shoptet\.cz)", obrazok):
                        result["obrazky_cudzia_domena"].append(data)
                    obrazky[obrazok].append(kod)

                if not ean:
                    result["produkty_bez_eanu"].append(data)
                elif not re.fullmatch(r"\d{8,13}", ean):
                    result["neplatne_ean_kody"].append(data)

                if not kategoria:
                    result["nezaradene_produkty"].append(data)

                if not vyrobca:
                    result["produkty_bez_vyrobcu"].append(data)

                kody[kod].append(nazov)

    except Exception as e:
        return {"chyba": f"Chyba pri spracovaní CSV: {e}", "typ_feedu": "woocommerce_csv"}

    for nazov, ids in nazvy.items():
        if len(ids) > 1:
            result["duplicitne_nazvy"].append(f"{nazov} ({', '.join(ids)})")

    for kod, nazvy_kodu in kody.items():
        if len(nazvy_kodu) > 1:
            result["duplicitne_kody"].append(kod)

    for url, produkty in obrazky.items():
        if len(produkty) > 1:
            result["obrazky_duplicita"].append(f"{url}: {', '.join(produkty)}")

    return result


async def run_audit(feed_path: str):
    try:
        if feed_path.startswith("http"):
            response = await httpx.get(feed_path)
            response.raise_for_status()
            raw_data = response.text
            is_remote = True
        else:
            if not os.path.exists(feed_path):
                return {"chyba": f"Lokálny súbor sa nenašiel: {feed_path}"}
            with open(feed_path, "r", encoding="utf-8") as file:
                raw_data = file.read()
            is_remote = False
    except Exception as e:
        return {"chyba": f"Chyba pri načítaní feedu: {e}"}

    typ_feedu = rozpoznaj_typ_feedu(raw_data)

    if typ_feedu == "woocommerce_csv":
        if is_remote:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8") as tmp:
                tmp.write(raw_data)
                tmp_path = tmp.name
        else:
            tmp_path = feed_path
        return audituj_woocommerce_csv(tmp_path)

    elif typ_feedu != "shoptet":
        return {"chyba": f"Nepodporovaný alebo neznámy typ feedu ({typ_feedu})", "typ_feedu": typ_feedu}

    # --- Shoptet XML audit ---
    try:
        root = ET.fromstring(raw_data)
    except Exception as e:
        return {"chyba": f"Chybný XML formát: {e}", "typ_feedu": "shoptet"}

    result = defaultdict(list)
    result["typ_feedu"] = "shoptet"

    for key in [
        "produkty_bez_nazvu",
        "produkty_bez_popisu",
        "produkty_s_kratkym_popisom",
        "dlhe_nazvy",
        "dlhe_popisy",
        "popis_rovnaky_ako_nazov",
        "produkty_bez_ceny",
        "produkty_s_cenou_nula",
        "nezvycajne_nizka_cena",
        "produkty_bez_obrazka",
        "neplatna_url_obrazka",
        "obrazky_cudzia_domena",
        "obrazky_duplicita",
        "nevhodne_znaky",
        "duplicitne_nazvy",
        "duplicitne_kody",
        "produkty_bez_eanu",
        "neplatne_ean_kody",
        "nezaradene_produkty",
        "produkty_bez_vyrobcu",
    ]:
        result[key] = []

    nazvy = defaultdict(list)
    kody = defaultdict(list)
    obrazky = defaultdict(list)

    for produkt in root.findall("SHOPITEM"):
        kod = produkt.findtext("ITEM_ID", default="(bez kódu)").strip()
        nazov = produkt.findtext("PRODUCT", default="").strip()
        popis = produkt.findtext("DESCRIPTION", default="").strip()
        cena = produkt.findtext("PRICE_VAT", default="").strip()
        obrazok = produkt.findtext("IMGURL", default="").strip()
        ean = produkt.findtext("EAN", default="").strip()
        kategoria = produkt.findtext("CATEGORYTEXT", default="").strip()
        vyrobca = produkt.findtext("MANUFACTURER", default="").strip()

        data = {"id": kod, "nazov": nazov}

        if not nazov:
            result["produkty_bez_nazvu"].append(data)
        else:
            nazvy[nazov].append(kod)
            if len(nazov) > 70:
                result["dlhe_nazvy"].append(data)

        if not popis:
            result["produkty_bez_popisu"].append(data)
        else:
            if len(popis) < 100:
                result["produkty_s_kratkym_popisom"].append(data)
            if len(popis) > 160:
                result["dlhe_popisy"].append(data)
            if nazov and nazov == popis:
                result["popis_rovnaky_ako_nazov"].append(data)
            if re.search(r'<[^>]+>|&[^;\s]+;', nazov + popis):
                result["nevhodne_znaky"].append(data)

        try:
            cena_val = float(cena)
            if cena_val <= 0.01:
                result["produkty_s_cenou_nula"].append(data)
            elif cena_val < 1.0:
                result["nezvycajne_nizka_cena"].append(data)
        except:
            result["produkty_bez_ceny"].append(data)

        if not obrazok:
            result["produkty_bez_obrazka"].append(data)
        else:
            if not obrazok.startswith("http"):  # VALIDÁCIA URL obrázka
                result["neplatna_url_obrazka"].append(data)
            if not re.search(r"(tvojeshop\.sk|myshoptet\.com|cdn\.shoptet\.cz)", obrazok):
                result["obrazky_cudzia_domena"].append(data)
            obrazky[obrazok].append(kod)

        if not ean:
            result["produkty_bez_eanu"].append(data)
        elif not re.fullmatch(r"\d{8,13}", ean):
            result["neplatne_ean_kody"].append(data)

        if not kategoria:
            result["nezaradene_produkty"].append(data)

        if not vyrobca:
            result["produkty_bez_vyrobcu"].append(data)

        kody[kod].append(nazov)

    for nazov, ids in nazvy.items():
        if len(ids) > 1:
            result["duplicitne_nazvy"].append(f"{nazov} ({', '.join(ids)})")

    for kod, nazvy_kodu in kody.items():
        if len(nazvy_kodu) > 1:
            result["duplicitne_kody"].append(kod)

    for url, produkty in obrazky.items():
        if len(produkty) > 1:
            result["obrazky_duplicita"].append(f"{url}: {', '.join(produkty)}")

    return result
