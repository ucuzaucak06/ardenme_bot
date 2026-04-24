import asyncio
import aiohttp
import logging
import json

logger = logging.getLogger(__name__)

BASE_URL = "https://partners.api.skyscanner.net/apiservices"

MARKETS = {
    "TR": ("TRY", "tr-TR"),
    "GB": ("GBP", "en-GB"),
    "US": ("USD", "en-US"),
    "DE": ("EUR", "de-DE"),
    "FR": ("EUR", "fr-FR"),
    "IT": ("EUR", "it-IT"),
    "ES": ("EUR", "es-ES"),
    "NL": ("EUR", "nl-NL"),
    "PL": ("PLN", "pl-PL"),
    "RO": ("RON", "ro-RO"),
    "HU": ("HUF", "hu-HU"),
    "CZ": ("CZK", "cs-CZ"),
    "GR": ("EUR", "el-GR"),
    "PT": ("EUR", "pt-PT"),
    "SE": ("SEK", "sv-SE"),
    "NO": ("NOK", "nb-NO"),
    "DK": ("DKK", "da-DK"),
    "FI": ("EUR", "fi-FI"),
    "AT": ("EUR", "de-AT"),
    "BE": ("EUR", "fr-BE"),
    "CH": ("CHF", "de-CH"),
    "RU": ("RUB", "ru-RU"),
    "UA": ("UAH", "uk-UA"),
    "AE": ("AED", "ar-AE"),
    "SA": ("SAR", "ar-SA"),
    "QA": ("QAR", "ar-QA"),
    "KW": ("KWD", "ar-KW"),
    "EG": ("EGP", "ar-EG"),
    "IL": ("ILS", "he-IL"),
    "IN": ("INR", "en-IN"),
    "JP": ("JPY", "ja-JP"),
    "KR": ("KRW", "ko-KR"),
    "CN": ("CNY", "zh-CN"),
    "SG": ("SGD", "en-SG"),
    "TH": ("THB", "th-TH"),
    "MY": ("MYR", "ms-MY"),
    "AU": ("AUD", "en-AU"),
    "NZ": ("NZD", "en-NZ"),
    "CA": ("CAD", "en-CA"),
    "MX": ("MXN", "es-MX"),
    "BR": ("BRL", "pt-BR"),
    "AR": ("ARS", "es-AR"),
    "ZA": ("ZAR", "en-ZA"),
    "NG": ("NGN", "en-NG"),
    "MA": ("MAD", "fr-MA"),
    "BG": ("BGN", "bg-BG"),
    "RS": ("RSD", "sr-RS"),
    "HR": ("EUR", "hr-HR"),
    "SK": ("EUR", "sk-SK"),
    "SI": ("EUR", "sl-SI"),
    "LT": ("EUR", "lt-LT"),
    "LV": ("EUR", "lv-LV"),
    "EE": ("EUR", "et-EE"),
    "HK": ("HKD", "zh-HK"),
    "TW": ("TWD", "zh-TW"),
    "ID": ("IDR", "id-ID"),
    "PH": ("PHP", "en-PH"),
    "VN": ("VND", "vi-VN"),
    "PK": ("PKR", "ur-PK"),
    "BD": ("BDT", "en-BD"),
    "LK": ("LKR", "si-LK"),
    "GE": ("GEL", "ka-GE"),
    "AZ": ("AZN", "az-AZ"),
    "KZ": ("KZT", "ru-KZ"),
    "UZ": ("UZS", "uz-UZ"),
    "JO": ("JOD", "ar-JO"),
    "IQ": ("IQD", "ar-IQ"),
    "MK": ("MKD", "mk-MK"),
    "AL": ("ALL", "sq-AL"),
    "ME": ("EUR", "sr-ME"),
    "BA": ("BAM", "bs-BA"),
    "MD": ("MDL", "ro-MD"),
    "AM": ("AMD", "hy-AM"),
    "BY": ("BYN", "ru-BY"),
    "IS": ("ISK", "is-IS"),
    "CY": ("EUR", "el-CY"),
    "MT": ("EUR", "en-MT"),
    "LU": ("EUR", "fr-LU"),
    "IE": ("EUR", "en-IE"),
}

EUR_RATES = {
    "EUR": 1.0, "TRY": 0.028, "GBP": 1.17, "USD": 0.92, "PLN": 0.23,
    "RON": 0.20, "HUF": 0.0026, "CZK": 0.041, "SEK": 0.087, "NOK": 0.085,
    "DKK": 0.134, "CHF": 1.02, "RUB": 0.010, "UAH": 0.022, "AED": 0.250,
    "SAR": 0.245, "QAR": 0.253, "KWD": 3.00, "EGP": 0.019, "ILS": 0.248,
    "INR": 0.011, "JPY": 0.0062, "KRW": 0.00067, "CNY": 0.127, "SGD": 0.685,
    "THB": 0.026, "MYR": 0.200, "AUD": 0.596, "NZD": 0.547, "CAD": 0.676,
    "MXN": 0.046, "BRL": 0.163, "ARS": 0.001, "ZAR": 0.048, "NGN": 0.00057,
    "MAD": 0.092, "BGN": 0.511, "RSD": 0.0085, "HKD": 0.118, "TWD": 0.028,
    "IDR": 0.000057, "PHP": 0.016, "VND": 0.000037, "PKR": 0.0033,
    "BDT": 0.0083, "LKR": 0.003, "GEL": 0.340, "AZN": 0.540, "KZT": 0.002,
    "UZS": 0.000073, "JOD": 1.30, "IQD": 0.0007, "MKD": 0.016, "ALL": 0.0097,
    "BAM": 0.511, "MDL": 0.052, "AMD": 0.0024, "BYN": 0.290, "ISK": 0.0068,
}


def to_eur(amount, currency):
    return round(float(amount) * EUR_RATES.get(currency, 1.0), 2)


def flag_emoji(code):
    return "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in code.upper())


async def query_market(session, api_key, market, currency, locale, origin, destination, depart_date, return_date=None):
    url = f"{BASE_URL}/v3/flights/indicative/search"
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    try:
        y, m, d = map(int, depart_date.split("-"))
    except Exception:
        return {"market": market, "price_eur": None, "error": "Tarih hatası"}

    legs = [{
        "originPlace": {"queryPlace": {"iata": origin}},
        "destinationPlace": {"queryPlace": {"iata": destination}},
        "fixedDate": {"year": y, "month": m, "day": d}
    }]

    if return_date:
        try:
            ry, rm, rd = map(int, return_date.split("-"))
            legs.append({
                "originPlace": {"queryPlace": {"iata": destination}},
                "destinationPlace": {"queryPlace": {"iata": origin}},
                "fixedDate": {"year": ry, "month": rm, "day": rd}
            })
        except Exception:
            pass

    body = {"query": {"market": market, "locale": locale, "currency": currency, "queryLegs": legs}}

    try:
        async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            text = await resp.text()
            if resp.status != 200:
                logger.debug(f"[{market}] HTTP {resp.status}: {text[:150]}")
                return {"market": market, "price_eur": None, "error": f"HTTP {resp.status}"}

            data = json.loads(text)

            # API quotes yapisi: content.results.quotes
            quotes = data.get("content", {}).get("results", {}).get("quotes", {})

            min_price = None
            for quote_id, quote in quotes.items():
                price_obj = quote.get("minPrice", {})
                raw = price_obj.get("amount")
                if raw is not None:
                    try:
                        val = float(raw)
                        # unit PRICE_UNIT_WHOLE ise tam sayi (kurus degil)
                        if val > 0 and (min_price is None or val < min_price):
                            min_price = val
                    except (ValueError, TypeError):
                        pass

            if min_price is None:
                return {"market": market, "price_eur": None, "error": "fiyat yok"}

            price_eur = to_eur(min_price, currency)
            return {"market": market, "currency": currency, "price_original": min_price, "price_eur": price_eur, "error": None}

    except asyncio.TimeoutError:
        return {"market": market, "price_eur": None, "error": "timeout"}
    except Exception as e:
        return {"market": market, "price_eur": None, "error": str(e)[:50]}


async def search_cheapest_market(api_key, origin, destination, depart_date, return_date=None):
    flight_type = "Gidiş-Dönüş" if return_date else "Tek Yön"
    results = []
    error_count = 0
    market_list = list(MARKETS.items())

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        BATCH = 10
        DELAY = 1.5
        for i in range(0, len(market_list), BATCH):
            batch = market_list[i:i + BATCH]
            tasks = [
                query_market(session, api_key, m, cur, loc, origin, destination, depart_date, return_date)
                for m, (cur, loc) in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in batch_results:
                if isinstance(r, Exception):
                    error_count += 1
                elif r.get("price_eur") is not None:
                    results.append(r)
                else:
                    error_count += 1
            if i + BATCH < len(market_list):
                await asyncio.sleep(DELAY)

    if not results:
        return (
            f"❌ *{origin} → {destination}* ({flight_type})\n\n"
            f"Skyscanner bu rota için önbelleğinde fiyat bulamadı.\n\n"
            f"• Bu rota az aranan olabilir\n"
            f"• Birkaç saat/gün sonra tekrar dene\n"
            f"• Farklı tarihle dene\n\n"
            f"_Sorgulanan: {len(market_list)} market | Hata/boş: {error_count}_"
        )

    results.sort(key=lambda x: x["price_eur"])
    top5 = results[:5]
    en_ucuz = top5[0]

    if return_date:
        header = f"✈️ *{origin} → {destination} → {origin}*\n📅 Gidiş: {depart_date} | Dönüş: {return_date}\n🎫 {flight_type}\n"
    else:
        header = f"✈️ *{origin} → {destination}*\n📅 {depart_date}\n🎫 {flight_type}\n"

    winner = (
        f"\n🏆 *EN UCUZ MARKET:*\n"
        f"{flag_emoji(en_ucuz['market'])} *{en_ucuz['market']}* — "
        f"*{en_ucuz['price_eur']:.0f} EUR*\n"
        f"_(Yerel: {en_ucuz['price_original']:.0f} {en_ucuz['currency']})_\n"
    )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    top5_text = "\n📊 *İlk 5 Market:*\n"
    for i, r in enumerate(top5):
        top5_text += f"{medals[i]} {flag_emoji(r['market'])} {r['market']} — {r['price_eur']:.0f} EUR _{r['price_original']:.0f} {r['currency']}_\n"

    # Tüm marketler listesi
    all_markets_text = "\n\n📋 *Tüm Fiyat Veren Marketler:*\n"
    for r in results:
        all_markets_text += f"{flag_emoji(r['market'])} {r['market']} — {r['price_eur']:.0f} EUR _({r['price_original']:.0f} {r['currency']})_\n"

    stats = f"\n📈 Sonuç bulunan: *{len(results)}* market | Yanıtsız: {error_count}"
    note = "\n\n_💡 Fiyatlar Skyscanner önbelleğinden gelir, 4 güne kadar eski olabilir._"

    return header + winner + top5_text + all_markets_text + stats + note
