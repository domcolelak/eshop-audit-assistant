# E-shop Audit Assistant

Tento projekt slúži na audit produktových XML a CSV feedov e-shopov.  
Automaticky vyhodnocuje chyby v dátach a ponúka AI návrhy na opravy.

## Funkcie

- Podpora Shoptet XML feedov  
- Podpora WooCommerce CSV feedov  
- Kontrola chýb ako chýbajúce názvy, popisy, ceny, obrázky, EAN kódy a ďalšie  
- Automatické generovanie návrhov opráv pomocou AI  
- Export výsledkov auditu do CSV súboru

## Inštalácia

1. Klonuj repozitár:

```bash
git clone https://github.com/tvoje-github-meno/eshop-audit-assistant.git
cd eshop-audit-assistant
Vytvor a aktivuj virtuálne prostredie:

bash
Kopírovať
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
Nainštaluj závislosti:

bash
Kopírovať
pip install -r requirements.txt
Spusti aplikáciu:

bash
Kopírovať
uvicorn app.main:app --reload
Otvor prehliadač na adrese:

cpp
Kopírovať
http://127.0.0.1:8000
Použitie
Nahraj XML alebo CSV súbor feedu alebo zadaj URL feedu (ak túto možnosť ponecháš) a spusti audit.

Prezri si chyby a návrhy opráv v prehľadnom rozhraní.

Exportuj výsledky do CSV pre ďalšie spracovanie.

Licencia
MIT License © 2025 Ing. Dominik Lelák
