import xml.etree.ElementTree as ET
import csv
import io

def rozpoznaj_typ_feedu(content: str) -> str:
    # Najprv sa pokúsime rozpoznať ako XML
    try:
        root = ET.fromstring(content)

        # Shoptet XML má root tag "SHOP" a pod ním "SHOPITEM"
        if root.tag.upper() == "SHOP" and root.find("SHOPITEM") is not None:
            return "shoptet"

        # WooCommerce XML (RSS feed)
        if root.tag.lower() == "rss":
            channel = root.find("channel")
            if channel is not None and channel.find("item") is not None:
                return "woocommerce"

        return "neznamy"
    except ET.ParseError:
        pass  # Nie je XML, skúsime CSV

    # Pokus o rozpoznanie CSV
    try:
        csv_reader = csv.reader(io.StringIO(content))
        headers = next(csv_reader)

        # WooCommerce CSV má zvyčajne tieto stĺpce:
        woo_headers = {"ID", "Name", "Type", "SKU", "Regular price", "Categories"}
        if any(h in headers for h in woo_headers):
            return "woocommerce_csv"
    except Exception:
        pass

    return "neznamy"
