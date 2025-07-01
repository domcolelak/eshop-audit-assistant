# E-shop Audit Assistant

Tento projekt slúži na audit produktových XML a CSV feedov e-shopov. Automaticky vyhodnocuje chyby v dátach a ponúka AI návrhy na opravy.

## Funkcie

- Podpora Shoptet XML feedov
- Podpora WooCommerce CSV feedov
- Kontrola chýb ako chýbajúce názvy, popisy, ceny, obrázky, EAN kódy a ďalšie
- Automatické generovanie návrhov opráv pomocou AI
- Export výsledkov auditu do CSV súboru

## Inštalácia

1. Klonuj repozitár:
git clone https://github.com/tvoje-github-meno/eshop-audit-assistant.git
cd eshop-audit-assistant

2. Vytvor a aktivuj virtuálne prostredie:

Windows:
python -m venv venv
venv\Scripts\activate

Linux/macOS:
python3 -m venv venv
source venv/bin/activate

3. Nainštaluj závislosti:
pip install -r requirements.txt

4. Spusti aplikáciu:
uvicorn app.main:app --reload

5. Otvor prehliadač na adrese:
http://127.0.0.1:8000

## Použitie

Nahraj XML alebo CSV súbor feedu a spusti audit. Prezri si chyby a návrhy opráv v prehľadnom rozhraní. Exportuj výsledky do CSV pre ďalšie spracovanie.

## Licencia

MIT License © 2025 Ing. Dominik Lelák
