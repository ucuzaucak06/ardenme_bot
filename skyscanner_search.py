import asyncio
import aiohttp
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://partners.api.skyscanner.net/apiservices"

# Skyscanner'ın desteklediği tüm marketler (ülke kodları)
# Bu liste /cultures/v1/markets endpoint'inden alınır
# Aşağıda tam liste hardcoded olarak var (API'dan çekmek yerine)
ALL_MARKETS = [
    "AF", "AX", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG",
    "AR", "AM", "AW", "AU", "AT", "AZ", "BS", "BH", "BD", "BB",
    "BY", "BE", "BZ", "BJ", "BM", "BT", "BO", "BQ", "BA", "BW",
    "BV", "BR", "IO", "BN", "BG", "BF", "BI", "CV", "KH", "CM",
    "CA", "KY", "CF", "TD", "CL", "CN", "CX", "CC", "CO", "KM",
    "CG", "CD", "CK", "CR", "CI", "HR", "CU", "CW", "CY", "CZ",
    "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER", "EE",
    "SZ", "ET", "FK", "FO", "FJ", "FI", "FR", "GF", "PF", "TF",
    "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD", "GP",
    "GU", "GT", "GG", "GN", "GW", "GY", "HT", "HM", "VA", "HN",
    "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IM", "IL",
    "IT", "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR",
    "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT",
    "LU", "MO", "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ",
    "MR", "MU", "YT", "MX", "FM", "MD", "MC", "MN", "ME", "MS",
    "MA", "MZ", "MM", "NA", "NR", "NP", "NL", "NC", "NZ", "NI",
    "NE", "NG", "NU", "NF", "MK", "MP", "NO", "OM", "PK", "PW",
    "PS", "PA", "PG", "PY", "PE", "PH", "PN", "PL", "PT", "PR",
    "QA", "RE", "RO", "RU", "RW", "BL", "SH", "KN", "LC", "MF",
    "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC", "SL",
    "SG", "SX", "SK", "SI", "SB", "SO", "ZA", "GS", "SS", "ES",
    "LK", "SD", "SR", "SJ", "SE", "CH", "SY", "TW", "TJ", "TZ",
    "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC",
    "TV", "UG", "UA", "AE", "GB", "US", "UM", "UY", "UZ", "VU",
    "VE", "VN", "VG", "VI", "WF", "EH", "YE", "ZM", "ZW"
]

# EUR dönüşüm için popüler para birimleri tablosu
# Gerçek zamanlı kur için ayrı bir API çağrısı yapılır
CURRENCY_MAP = {
    "AF": ("AFN", "en-GB"),
    "AL": ("ALL", "en-GB"),
    "DZ": ("DZD", "en-GB"),
    "AR": ("ARS", "en-GB"),
    "AM": ("AMD", "en-GB"),
    "AU": ("AUD", "en-AU"),
    "AT": ("EUR", "de-AT"),
    "AZ": ("AZN", "en-GB"),
    "BS": ("BSD", "en-GB"),
    "BH": ("BHD", "en-GB"),
    "BD": ("BDT", "en-GB"),
    "BY": ("BYN", "en-GB"),
    "BE": ("EUR", "fr-BE"),
    "BZ": ("BZD", "en-GB"),
    "BT": ("BTN", "en-GB"),
    "BO": ("BOB", "es-BO"),
    "BA": ("BAM", "en-GB"),
    "BW": ("BWP", "en-GB"),
    "BR": ("BRL", "pt-BR"),
    "BN": ("BND", "en-GB"),
    "BG": ("BGN", "bg-BG"),
    "CA": ("CAD", "en-CA"),
    "CL": ("CLP", "es-CL"),
    "CN": ("CNY", "zh-CN"),
    "CO": ("COP", "es-CO"),
    "CR": ("CRC", "es-CR"),
    "HR": ("EUR", "hr-HR"),
    "CU": ("CUP", "es-CU"),
    "CY": ("EUR", "el-CY"),
    "CZ": ("CZK", "cs-CZ"),
    "DK": ("DKK", "da-DK"),
    "DO": ("DOP", "es-DO"),
    "EC": ("USD", "es-EC"),
    "EG": ("EGP", "ar-EG"),
    "SV": ("USD", "es-SV"),
    "EE": ("EUR", "et-EE"),
    "ET": ("ETB", "en-GB"),
    "FI": ("EUR", "fi-FI"),
    "FR": ("EUR", "fr-FR"),
    "GE": ("GEL", "ka-GE"),
    "DE": ("EUR", "de-DE"),
    "GH": ("GHS", "en-GB"),
    "GR": ("EUR", "el-GR"),
    "GT": ("GTQ", "es-GT"),
    "HN": ("HNL", "es-HN"),
    "HK": ("HKD", "zh-HK"),
    "HU": ("HUF", "hu-HU"),
    "IS": ("ISK", "is-IS"),
    "IN": ("INR", "en-IN"),
    "ID": ("IDR", "id-ID"),
    "IQ": ("IQD", "ar-IQ"),
    "IE": ("EUR", "en-IE"),
    "IL": ("ILS", "he-IL"),
    "IT": ("EUR", "it-IT"),
    "JM": ("JMD", "en-GB"),
    "JP": ("JPY", "ja-JP"),
    "JO": ("JOD", "ar-JO"),
    "KZ": ("KZT", "ru-KZ"),
    "KE": ("KES", "en-GB"),
    "KR": ("KRW", "ko-KR"),
    "KW": ("KWD", "ar-KW"),
    "KG": ("KGS", "ru-KG"),
    "LA": ("LAK", "en-GB"),
    "LV": ("EUR", "lv-LV"),
    "LB": ("LBP", "ar-LB"),
    "LY": ("LYD", "ar-LY"),
    "LI": ("CHF", "de-LI"),
    "LT": ("EUR", "lt-LT"),
    "LU": ("EUR", "fr-LU"),
    "MO": ("MOP", "zh-MO"),
    "MG": ("MGA", "en-GB"),
    "MY": ("MYR", "ms-MY"),
    "MV": ("MVR", "en-GB"),
    "MT": ("EUR", "en-MT"),
    "MX": ("MXN", "es-MX"),
    "MD": ("MDL", "ro-MD"),
    "MC": ("EUR", "fr-MC"),
    "MN": ("MNT", "mn-MN"),
    "ME": ("EUR", "sr-ME"),
    "MA": ("MAD", "fr-MA"),
    "MZ": ("MZN", "pt-MZ"),
    "MM": ("MMK", "en-GB"),
    "NA": ("NAD", "en-GB"),
    "NP": ("NPR", "ne-NP"),
    "NL": ("EUR", "nl-NL"),
    "NZ": ("NZD", "en-NZ"),
    "NI": ("NIO", "es-NI"),
    "NG": ("NGN", "en-NG"),
    "MK": ("MKD", "mk-MK"),
    "NO": ("NOK", "nb-NO"),
    "OM": ("OMR", "ar-OM"),
    "PK": ("PKR", "ur-PK"),
    "PA": ("PAB", "es-PA"),
    "PG": ("PGK", "en-GB"),
    "PY": ("PYG", "es-PY"),
    "PE": ("PEN", "es-PE"),
    "PH": ("PHP", "en-PH"),
    "PL": ("PLN", "pl-PL"),
    "PT": ("EUR", "pt-PT"),
    "QA": ("QAR", "ar-QA"),
    "RO": ("RON", "ro-RO"),
    "RU": ("RUB", "ru-RU"),
    "RW": ("RWF", "en-GB"),
    "SA": ("SAR", "ar-SA"),
    "SN": ("XOF", "fr-SN"),
    "RS": ("RSD", "sr-RS"),
    "SC": ("SCR", "en-GB"),
    "SG": ("SGD", "en-SG"),
    "SK": ("EUR", "sk-SK"),
    "SI": ("EUR", "sl-SI"),
    "ZA": ("ZAR", "en-ZA"),
    "ES": ("EUR", "es-ES"),
    "LK": ("LKR", "si-LK"),
    "SD": ("SDG", "ar-SD"),
    "SE": ("SEK", "sv-SE"),
    "CH": ("CHF", "de-CH"),
    "TW": ("TWD", "zh-TW"),
    "TJ": ("TJS", "tg-TJ"),
    "TZ": ("TZS", "en-GB"),
    "TH": ("THB", "th-TH"),
    "TN": ("TND", "ar-TN"),
    "TR": ("TRY", "tr-TR"),
    "TM": ("TMT", "tk-TM"),
    "UG": ("UGX", "en-GB"),
    "UA": ("UAH", "uk-UA"),
    "AE": ("AED", "ar-AE"),
    "GB": ("GBP", "en-GB"),
    "US": ("USD", "en-US"),
    "UY": ("UYU", "es-UY"),
    "UZ": ("UZS", "uz-UZ"),
    "VE": ("VES", "es-VE"),
    "VN": ("VND", "vi-VN"),
    "YE": ("YER", "ar-YE"),
    "ZM": ("ZMW", "en-GB"),
    "ZW": ("ZWL", "en-GB"),
}

# EUR bazlı yaklaşık kurlar (günlük güncellenmesi önerilir)
# Bot bu kurlarla dönüşüm yapar
EUR_RATES = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "TRY": 0.028,
    "AED": 0.25,
    "SAR": 0.245,
    "QAR": 0.253,
    "KWD": 3.0,
    "BHD": 2.45,
    "OMR": 2.39,
    "JOD": 1.3,
    "EGP": 0.019,
    "MAD": 0.092,
    "TND": 0.29,
    "LYD": 0.19,
    "DZD": 0.0068,
    "DKK": 0.134,
    "SEK": 0.087,
    "NOK": 0.085,
    "CHF": 1.02,
    "PLN": 0.23,
    "CZK": 0.041,
    "HUF": 0.0026,
    "RON": 0.2,
    "BGN": 0.51,
    "RSD": 0.0085,
    "HRK": 0.133,
    "MKD": 0.016,
    "ALL": 0.0097,
    "BAM": 0.51,
    "MDL": 0.052,
    "UAH": 0.022,
    "RUB": 0.01,
    "BYN": 0.29,
    "GEL": 0.34,
    "AZN": 0.54,
    "AMD": 0.0024,
    "KZT": 0.002,
    "UZS": 0.000073,
    "KGS": 0.011,
    "TJS": 0.086,
    "TMT": 0.263,
    "MNT": 0.00027,
    "JPY": 0.0062,
    "CNY": 0.127,
    "KRW": 0.00067,
    "TWD": 0.028,
    "HKD": 0.118,
    "SGD": 0.685,
    "MYR": 0.2,
    "THB": 0.026,
    "IDR": 0.000057,
    "PHP": 0.016,
    "VND": 0.000037,
    "INR": 0.011,
    "PKR": 0.0033,
    "BDT": 0.0083,
    "LKR": 0.003,
    "NPR": 0.0069,
    "MMK": 0.00043,
    "KHR": 0.00022,
    "LAK": 0.000043,
    "MVR": 0.059,
    "AUD": 0.596,
    "NZD": 0.547,
    "CAD": 0.676,
    "MXN": 0.046,
    "BRL": 0.163,
    "ARS": 0.001,
    "CLP": 0.00097,
    "COP": 0.00022,
    "PEN": 0.245,
    "BOB": 0.133,
    "PYG": 0.000123,
    "UYU": 0.023,
    "VES": 0.026,
    "ZAR": 0.048,
    "NGN": 0.00057,
    "KES": 0.0071,
    "GHS": 0.059,
    "TZS": 0.00034,
    "UGX": 0.00024,
    "RWF": 0.00066,
    "ETB": 0.0072,
    "MAD": 0.092,
    "XOF": 0.00153,
    "XAF": 0.00153,
    "DOP": 0.016,
    "GTQ": 0.119,
    "HNL": 0.038,
    "NIO": 0.025,
    "CRC": 0.0017,
    "PAB": 0.92,
    "JMD": 0.0059,
    "TTD": 0.136,
    "BZD": 0.456,
    "ILS": 0.248,
    "IQD": 0.0007,
    "LBP": 0.00001,
    "SYP": 0.00007,
    "YER": 0.0037,
    "AFN": 0.013,
}


async def get_eur_rate(currency: str) -> float:
    """Verilen para birimini EUR'a çevirme katsayısını döndürür"""
    return EUR_RATES.get(currency, 1.0)


async def search_market(
    session: aiohttp.ClientSession,
    api_key: str,
    market: str,
    currency: str,
    locale: str,
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str = None
) -> dict:
    """Tek bir market için Skyscanner Indicative API'yi sorgular"""
    
    url = f"{BASE_URL}/v3/flights/indicative/search"
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Tarih formatını API için hazırla (YYYY-MM-DD → yıl, ay, gün)
    try:
        d = datetime.strptime(depart_date, "%Y-%m-%d")
        depart_year, depart_month, depart_day = d.year, d.month, d.day
    except ValueError:
        return {"market": market, "price": None, "error": "Geçersiz tarih formatı"}

    query = {
        "market": market,
        "locale": locale,
        "currency": currency,
        "queryLegs": [
            {
                "originPlace": {"queryPlace": {"iata": origin}},
                "destinationPlace": {"queryPlace": {"iata": destination}},
                "fixedDate": {
                    "year": depart_year,
                    "month": depart_month,
                    "day": depart_day
                }
            }
        ]
    }

    if return_date:
        try:
            r = datetime.strptime(return_date, "%Y-%m-%d")
            query["queryLegs"].append({
                "originPlace": {"queryPlace": {"iata": destination}},
                "destinationPlace": {"queryPlace": {"iata": origin}},
                "fixedDate": {
                    "year": r.year,
                    "month": r.month,
                    "day": r.day
                }
            })
        except ValueError:
            pass

    try:
        async with session.post(url, json={"query": query}, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                data = await response.json()
                
                # Sonuçlardan minimum fiyatı çıkar
                itineraries = data.get("content", {}).get("results", {}).get("itineraries", {})
                
                min_price = None
                for key, itinerary in itineraries.items():
                    pricing = itinerary.get("pricingOptions", [])
                    for option in pricing:
                        price = option.get("price", {}).get("amount")
                        if price:
                            try:
                                price_float = float(price)
                                if min_price is None or price_float < min_price:
                                    min_price = price_float
                            except (ValueError, TypeError):
                                pass
                
                return {
                    "market": market,
                    "currency": currency,
                    "price_original": min_price,
                    "error": None
                }
            elif response.status == 429:
                return {"market": market, "price": None, "error": "Rate limit"}
            else:
                return {"market": market, "price": None, "error": f"HTTP {response.status}"}
    except asyncio.TimeoutError:
        return {"market": market, "price": None, "error": "Timeout"}
    except Exception as e:
        return {"market": market, "price": None, "error": str(e)[:50]}


async def search_cheapest_market(
    api_key: str,
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str = None
) -> str:
    """
    Skyscanner'ın tüm marketlerinde arama yaparak en ucuz sonucu döndürür.
    Rate limit aşımını önlemek için market listesini gruplar halinde sorgular.
    """
    
    flight_type = "Gidiş-Dönüş" if return_date else "Tek Yön"
    
    # Hangi marketleri sorgulayacağız
    # Rate limit koruma: sadece currency_map'te olan marketleri kullan
    markets_to_search = [(market, *CURRENCY_MAP[market]) for market in ALL_MARKETS if market in CURRENCY_MAP]
    
    results = []
    errors = []
    
    # Rate limit aşmamak için marketleri küçük gruplar halinde işle
    BATCH_SIZE = 15
    DELAY_BETWEEN_BATCHES = 2  # saniye
    
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(0, len(markets_to_search), BATCH_SIZE):
            batch = markets_to_search[i:i + BATCH_SIZE]
            
            tasks = [
                search_market(
                    session=session,
                    api_key=api_key,
                    market=market,
                    currency=currency,
                    locale=locale,
                    origin=origin,
                    destination=destination,
                    depart_date=depart_date,
                    return_date=return_date
                )
                for market, currency, locale in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                    continue
                
                if result.get("price_original") is not None:
                    currency = result.get("currency", "USD")
                    eur_rate = await get_eur_rate(currency)
                    price_eur = result["price_original"] * eur_rate
                    result["price_eur"] = round(price_eur, 2)
                    results.append(result)
                elif result.get("error"):
                    errors.append(f"{result['market']}: {result['error']}")
            
            # Son batch değilse bekle
            if i + BATCH_SIZE < len(markets_to_search):
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)
    
    # Sonuçları fiyata göre sırala
    if not results:
        return (
            f"❌ *{origin} → {destination}* ({flight_type})\n\n"
            f"Hiçbir markette sonuç bulunamadı.\n"
            f"• Tarih kontrol edin\n"
            f"• IATA kodları doğru olmalı\n"
            f"• Bu rota bazı marketlerde mevcut olmayabilir"
        )
    
    results.sort(key=lambda x: x["price_eur"])
    
    # En ucuz 5 marketi al
    top5 = results[:5]
    cheapest = top5[0]
    
    # Emoji bayraklar için ülke kodu → emoji dönüşümü
    def flag(code):
        return "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in code.upper())
    
    # Sonuç mesajı oluştur
    if return_date:
        header = f"✈️ *{origin} → {destination} → {origin}*\n📅 {depart_date} | 🔄 {return_date}\n🎫 {flight_type}\n"
    else:
        header = f"✈️ *{origin} → {destination}*\n📅 {depart_date}\n🎫 {flight_type}\n"
    
    winner_line = (
        f"\n🏆 *EN UCUZ MARKET:*\n"
        f"{flag(cheapest['market'])} *{cheapest['market']}* — "
        f"*{cheapest['price_eur']:.0f} EUR*\n"
        f"(Yerel fiyat: {cheapest['price_original']:.0f} {cheapest['currency']})\n"
    )
    
    top5_lines = "\n📊 *İlk 5 Market:*\n"
    for i, r in enumerate(top5, 1):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
        top5_lines += f"{medal} {flag(r['market'])} {r['market']} — {r['price_eur']:.0f} EUR ({r['price_original']:.0f} {r['currency']})\n"
    
    stats_line = f"\n📈 *Taranan market:* {len(results)} | *Sonuçsuz:* {len(errors)}"
    
    note = "\n\n_💡 Fiyatlar gösterge niteliğindedir. Kur dönüşümleri yaklaşık değerdir._"
    
    return header + winner_line + top5_lines + stats_line + note
