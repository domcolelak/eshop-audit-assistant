REPAIR_SUGGESTIONS_COMMON = {
    "produkty_bez_nazvu": "Doplňte názvy produktov – bez nich sa produkt nezobrazí vo výsledkoch vyhľadávania.",
    "produkty_bez_popisu": "Doplňte popisy – zákazníci sa musia dozvedieť, čo kupujú.",
    "produkty_s_kratkym_popisom": "Zvážte rozšírenie popisu na aspoň 100 znakov kvôli SEO a UX.",
    "dlhe_nazvy": "Skráťte názov pod 70 znakov – dlhé názvy sa môžu zle zobrazovať.",
    "dlhe_popisy": "Zvážte skrátenie popisu pod 160 znakov, ideálne pre zobrazenie vo vyhľadávačoch.",
    "popis_rovnaky_ako_nazov": "Rozlíšte popis od názvu – opakovanie znižuje kvalitu obsahu.",
    "produkty_bez_ceny": "Doplňte ceny – bez nich sa produkt nedá kúpiť.",
    "produkty_s_cenou_nula": "Skontrolujte chybnú alebo neplatnú cenu (0).",
    "produkty_bez_obrazka": "Pridajte obrázok produktu – bez vizuálu sa nepredáva.",
    "obrazky_cudzia_domena": "Nahrajte obrázky na vlastnú doménu kvôli rýchlosti a spoľahlivosti.",
    "obrazky_duplicita": "Zmeňte duplicitu obrázkov – viaceré produkty majú rovnaký obrázok.",
    "nevhodne_znaky": "Odstráňte neplatné HTML znaky z popisov/názvov.",
    "duplicitne_nazvy": "Rozlíšte produkty od seba – duplicitné názvy mätú zákazníkov.",
    "duplicitne_kody": "Každý produkt by mal mať jedinečný ITEM_ID.",
    "produkty_bez_eanu": "Doplňte EAN – využívaný pre porovnávače cien a skladové systémy.",
    "neplatne_ean_kody": "EAN kód musí mať 8 až 13 číslic – skontrolujte jeho formát.",
    "nezaradene_produkty": "Priraďte produkt ku kategórii – nezaradené produkty sa môžu stratiť.",
    "nezvycajne_nizka_cena": "Skontrolujte veľmi nízke ceny – mohlo ísť o chybu v zadávaní.",
    "produkty_bez_vyrobcu": "Doplňte značku alebo výrobcu – zvyšuje dôveryhodnosť produktu.",
}

REPAIR_SUGGESTIONS_WOOCOMMERCE = {
    "produkty_bez_nazvu": "Zadajte názov produktu v CSV exporte WooCommerce, bez neho nebude viditeľný.",
    "produkty_bez_popisu": "Pridajte detailný popis produktu pre lepšiu konverziu.",
    "produkty_bez_ceny": "Skontrolujte cenu v poli 'Regular price' v CSV WooCommerce exporte.",
    # ostatné chyby použijú spoločné návrhy
}

def navrh_na_zaklade_chyby(typ: str, data: dict, typ_feedu: str = "shoptet") -> str:
    if typ_feedu == "woocommerce_csv":
        suggestions = REPAIR_SUGGESTIONS_WOOCOMMERCE
        default = REPAIR_SUGGESTIONS_WOOCOMMERCE.get(typ) or REPAIR_SUGGESTIONS_COMMON.get(typ, "Navrhovaná oprava nie je dostupná.")
    else:
        suggestions = REPAIR_SUGGESTIONS_COMMON
        default = REPAIR_SUGGESTIONS_COMMON.get(typ, "Navrhovaná oprava nie je dostupná.")

    id_part = f" (ID: {data.get('id', '')})" if data.get("id") else ""
    nazov_part = f" „{data.get('nazov', '')}“" if data.get("nazov") else ""

    if typ == "produkty_bez_nazvu":
        if typ_feedu == "woocommerce_csv":
            return f"Zadajte názov produktu{nazov_part} v CSV exporte WooCommerce, bez neho nebude viditeľný."
        return f"Zadajte názov produktu{id_part} podľa EAN alebo kategórie."
    elif typ == "produkty_bez_popisu":
        if typ_feedu == "woocommerce_csv":
            return f"Pridajte detailný popis produktu{nazov_part} pre lepšiu konverziu v e-shope."
        return f"Pridajte popis produktu{nazov_part}, aby zákazník vedel, čo kupuje."
    elif typ == "produkty_bez_ceny" and typ_feedu == "woocommerce_csv":
        return f"Skontrolujte cenu v poli 'Regular price' pre produkt{nazov_part} v CSV WooCommerce exporte."
    else:
        return default
