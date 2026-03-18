"""
RESPiRE Backend - FastAPI v3.0
Hackathon KAIKAI 2025 • Équipe Breath4Life

Intégration AirGradient API v1 — champs réels :
  pm02_corrected  → PM2.5
  pm10_corrected  → PM10
  pm01_corrected  → PM1.0
  rco2_corrected  → CO₂
  atmp_corrected  → Température
  rhum_corrected  → Humidité
  tvoc            → COV totaux
  noxIndex        → NOx
  pm003Count      → PM0.3 (count)
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import logging
import httpx
# smtplib non utilisé (Railway bloque SMTP) — remplacé par Resend HTTP API
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, UploadFile, File as FastAPIFile
from fastapi.responses import JSONResponse
import base64
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="RESPiRE API",
    version="3.0.0",
    description="Backend RESPiRE — Qualité de l'air dans les écoles sénégalaises (AirGradient réel)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Configuration ────────────────────────────────────────────────────────────
AG_TOKEN      = os.getenv("AIRGRADIENT_TOKEN", "2122a271-e910-4ad8-acb8-5a24e764499b")  # token visible dans api_handler__.py
AG_BASE_URL   = "https://api.airgradient.com/public/api/v1"
CACHE_TTL     = int(os.getenv("CACHE_TTL", "120"))   # secondes

# ─── Email via Resend API (HTTP — pas de SMTP bloqué) ────────────────────────
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")          # clé API Resend
ALERT_EMAIL    = os.getenv("ALERT_EMAIL", "")              # email destinataire
ALERT_FROM     = os.getenv("ALERT_FROM", "RESPiRE <onboarding@resend.dev>")

# Fallback SMTP (si configuré)
SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER", "")
SMTP_PASS  = os.getenv("SMTP_PASS", "")

# Seuils OMS/EPA utilisés dans votre functions.py (VALEURS_LIMITE)
VALEURS_LIMITE = {
    "pm02_corrected": 25.0,    # PM2.5 OMS μg/m³/24h
    "pm10_corrected": 50.0,    # PM10  OMS μg/m³/24h
    "rco2_corrected": 1000.0,  # CO2   ppm seuil confort
    "tvoc":           300.0,   # COV   μg/m³
    "noxIndex":       100.0,   # NOx   index
}

# ─── Mapping écoles → locationId AirGradient ─────────────────────────────────
# locationId = l'ID réel fourni par AirGradient pour chaque capteur installé
# Remplacez ces valeurs par les vrais IDs de vos capteurs KAIKAI

SCHOOLS_CONFIG: List[Dict[str, Any]] = [
    # ── Thiès ──────────────────────────────────────────────────────────────────
    {"id": "01", "location_id": "89441",  "name": "Université Iba Der Thiam",                   "city": "Thiès",        "lat": 14.7800, "lng": -16.9260},
    {"id": "09", "location_id": "166062", "name": "Ecole Elémentaire Sud Stade",                "city": "Thiès",        "lat": 14.7850, "lng": -16.9350},
    {"id": "14", "location_id": "168373", "name": "Hôtel de Ville de Thiès",                    "city": "Thiès",        "lat": 14.7910, "lng": -16.9260},
    {"id": "17", "location_id": "168377", "name": "Lycée Malick Sy",                            "city": "Thiès",        "lat": 14.7900, "lng": -16.9300},
    {"id": "25", "location_id": "168388", "name": "Lycée Jules Sagna",                          "city": "Thiès",        "lat": 14.7860, "lng": -16.9280},
    {"id": "29", "location_id": "168397", "name": "Collège Cité Lamy",                          "city": "Thiès",        "lat": 14.7830, "lng": -16.9400},
    {"id": "31", "location_id": "168401", "name": "Lycée de FAHU",                              "city": "Thiès",        "lat": 14.7880, "lng": -16.9350},
    # ── Dakar ──────────────────────────────────────────────────────────────────
    {"id": "07", "location_id": "164250", "name": "Ecole Saint-Exupéry",                        "city": "Dakar",        "lat": 14.6928, "lng": -17.4467},
    {"id": "08", "location_id": "164928", "name": "ESMT — Ecole Sup. Multinationale des Télécoms", "city": "Dakar",    "lat": 14.7167, "lng": -17.4677},
    {"id": "15", "location_id": "168374", "name": "Ecole Aimé Césaire",                         "city": "Dakar",        "lat": 14.7617, "lng": -17.4828},
    {"id": "21", "location_id": "168381", "name": "Ecole Seydina Issa Laye B (Cambérène)",      "city": "Dakar",        "lat": 14.7600, "lng": -17.4820},
    {"id": "23", "location_id": "168386", "name": "Ecole Elhadj Mbaye Diop (Ouakam)",           "city": "Dakar",        "lat": 14.7333, "lng": -17.4833},
    {"id": "28", "location_id": "168395", "name": "Complexe Scolaire Limamoulaye",              "city": "Dakar",        "lat": 14.7737, "lng": -17.4066},
    {"id": "30", "location_id": "168400", "name": "CEM Martin Luther King",                     "city": "Dakar",        "lat": 14.7050, "lng": -17.4400},
    {"id": "32", "location_id": "168402", "name": "Lycée Blaise Diagne",                        "city": "Dakar",        "lat": 14.6928, "lng": -17.4467},
    {"id": "33", "location_id": "168405", "name": "Ecole Tivaoune Diacksao",                    "city": "Dakar",        "lat": 14.7542, "lng": -17.3953},
    {"id": "39", "location_id": "180099", "name": "Groupe Scolaire Asselar",                    "city": "Dakar",        "lat": 14.7050, "lng": -17.4400},
    # ── Saint-Louis ────────────────────────────────────────────────────────────
    {"id": "02", "location_id": "90104",  "name": "Lycée Technique André Peytavin",             "city": "Saint-Louis",  "lat": 16.0178, "lng": -16.4900},
    {"id": "26", "location_id": "168389", "name": "Ecole Goxu Mbacc 2",                         "city": "Saint-Louis",  "lat": 16.0100, "lng": -16.4850},
    {"id": "27", "location_id": "168391", "name": "CEM Guinaw Rails",                           "city": "Saint-Louis",  "lat": 16.0050, "lng": -16.4800},
    {"id": "37", "location_id": "176747", "name": "CEM André Peytavin (Nouveau)",               "city": "Saint-Louis",  "lat": 16.0178, "lng": -16.4900},
    {"id": "38", "location_id": "177055", "name": "Ecole Moussa Diop",                          "city": "Saint-Louis",  "lat": 16.0260, "lng": -16.5000},
    # ── Richard-Toll & Ross Bethio ─────────────────────────────────────────────
    {"id": "03", "location_id": "90106",  "name": "Ecole Elémentaire Ndiangué",                 "city": "Richard-Toll", "lat": 16.0333, "lng": -15.7000},
    {"id": "18", "location_id": "168378", "name": "Pharmacie de Ross Bethio",                   "city": "Ross Bethio",  "lat": 16.1000, "lng": -15.5500},
    {"id": "20", "location_id": "168380", "name": "Poste de Santé Ndiangué-Ndiaw",              "city": "Richard Toll", "lat": 16.0950, "lng": -15.5600},
    # ── Rufisque ───────────────────────────────────────────────────────────────
    {"id": "04", "location_id": "151674", "name": "Lycée de Bargny",                            "city": "Rufisque",     "lat": 14.7153, "lng": -17.2733},
    {"id": "36", "location_id": "176743", "name": "Hôpital Youssou Mbarguane",                  "city": "Rufisque",     "lat": 14.7153, "lng": -17.2733},
    # ── Diourbel ───────────────────────────────────────────────────────────────
    {"id": "05", "location_id": "151722", "name": "Lycée Cheikh Mouhamadou Moustapha Mbacké",   "city": "Diourbel",     "lat": 14.6556, "lng": -16.2294},
    {"id": "06", "location_id": "151726", "name": "Ecole Notre Dame des Victoires",             "city": "Diourbel",     "lat": 14.6600, "lng": -16.2250},
    # ── Keur Massar & Diacksao ─────────────────────────────────────────────────
    {"id": "11", "location_id": "168369", "name": "Ecole Publique Médina Gana Sarr (Mbeubeuss)", "city": "Keur Massar", "lat": 14.7300, "lng": -17.3200},
    {"id": "12", "location_id": "168371", "name": "Ecole Mbaye Diouf",                          "city": "Diacksao",     "lat": 14.7400, "lng": -17.3500},
    # ── Diamniadio ─────────────────────────────────────────────────────────────
    {"id": "13", "location_id": "168372", "name": "Université Amadou Mahtar Mbow (UAM)",        "city": "Diamniadio",   "lat": 14.7250, "lng": -17.0450},
    {"id": "24", "location_id": "168387", "name": "ISEP Diamniadio",                            "city": "Diamniadio",   "lat": 14.7250, "lng": -17.0450},
    # ── Ziguinchor ─────────────────────────────────────────────────────────────
    {"id": "10", "location_id": "168368", "name": "Hôpital de la Paix",                         "city": "Ziguinchor",   "lat": 12.5600, "lng": -16.2700},
    {"id": "16", "location_id": "168376", "name": "Lycée Djignabo",                             "city": "Ziguinchor",   "lat": 12.5620, "lng": -16.2690},
    {"id": "19", "location_id": "168379", "name": "CEM Boucotte Sud",                           "city": "Ziguinchor",   "lat": 12.5650, "lng": -16.2720},
    {"id": "22", "location_id": "168382", "name": "CEM Malick Fall",                            "city": "Ziguinchor",   "lat": 12.5580, "lng": -16.2750},
    # ── Bignona & Cap Skirring ─────────────────────────────────────────────────
    {"id": "34", "location_id": "168406", "name": "Lycée Ahoune Sané",                          "city": "Bignona",      "lat": 12.9800, "lng": -16.2500},
    {"id": "35", "location_id": "175981", "name": "Aéroport de Cap Skirring",                   "city": "Cap Skirring", "lat": 12.3800, "lng": -16.7500},
]

# ─── Cache mémoire ────────────────────────────────────────────────────────────
_cache: Dict[str, tuple] = {}

def cache_get(key: str) -> Optional[Any]:
    if key in _cache:
        data, ts = _cache[key]
        if (datetime.now() - ts).seconds < CACHE_TTL:
            return data
    return None

def cache_set(key: str, data: Any) -> None:
    _cache[key] = (data, datetime.now())

# ─── Modèles Pydantic ─────────────────────────────────────────────────────────

class AirData(BaseModel):
    # Données principales affichées dans l'app Flutter
    pm25: float        # pm02_corrected
    pm10: float        # pm10_corrected
    co2: float         # rco2_corrected
    temperature: float # atmp_corrected
    humidity: float    # rhum_corrected
    # Données supplémentaires
    pm1: float = 0.0   # pm01_corrected
    tvoc: float = 0.0
    nox: float = 0.0
    pm03_count: float = 0.0
    # IQA calculé
    aqi: int
    iqa: float         # IQA selon la méthode de votre functions.py
    aqi_level: str
    # Métadonnées
    last_updated: str
    source: str = "airgradient"  # "airgradient" | "mock"

class School(BaseModel):
    id: str
    name: str
    city: str
    lat: float
    lng: float
    aqi: int
    iqa: float = 0.0
    air_data: Optional[AirData] = None

class AlertRequest(BaseModel):
    school: str
    description: str
    photo_base64: Optional[str] = None   # Photo encodée en base64 (optionnel)
    photo_filename: Optional[str] = None # Nom du fichier photo (optionnel)

class SchoolDropdownItem(BaseModel):
    id: str
    name: str
    city: str
    display: str  # "Nom — Ville" pour l'affichage dans le dropdown

# ─── Calcul IQA (méthode identique à functions.py) ───────────────────────────

def calculer_iqa(mesures: Dict[str, float]) -> float:
    """
    Calcule l'IQA selon la méthode de votre functions.py :
    iqa_polluant = (concentration / limite) * 100
    IQA = max des IQA par polluant
    """
    iqa_values = {}
    for polluant, limite in VALEURS_LIMITE.items():
        if polluant in mesures and mesures[polluant] is not None:
            val = float(mesures[polluant])
            if val >= 0:
                iqa_values[polluant] = (val / limite) * 100.0

    if not iqa_values:
        return 0.0

    return round(max(iqa_values.values()), 2)

def compute_aqi_epa(pm25: float) -> int:
    """
    Calcul AQI US EPA standard à partir du PM2.5.
    Utilisé pour la compatibilité avec les standards internationaux.
    """
    breakpoints = [
        (0.0,   12.0,   0,   50),
        (12.1,  35.4,   51,  100),
        (35.5,  55.4,   101, 150),
        (55.5,  150.4,  151, 200),
        (150.5, 250.4,  201, 300),
        (250.5, 500.4,  301, 500),
    ]
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= pm25 <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + i_lo)
    return 500 if pm25 > 500 else 0

def get_aqi_level(aqi: int) -> str:
    if aqi <= 50:  return "Excellent"
    if aqi <= 100: return "Bon"
    if aqi <= 150: return "Moyen"
    if aqi <= 200: return "Mauvais"
    return "Très mauvais"

# ─── Parser réponse AirGradient ───────────────────────────────────────────────

def parse_ag_measure(raw: Dict[str, Any]) -> Optional[AirData]:
    """
    Parse un objet mesure AirGradient.
    Champs réels observés dans votre functions.py :
      pm02_corrected, pm10_corrected, pm01_corrected,
      rco2_corrected, atmp_corrected, rhum_corrected,
      tvoc, noxIndex, pm003Count
    """
    try:
        def _get(keys, default=0.0):
            """Essaie plusieurs noms de champs, retourne le premier trouvé."""
            for k in keys:
                v = raw.get(k)
                if v is not None:
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        pass
            return default

        pm25 = _get(["pm02_corrected", "pm02", "pm25", "pm2_5"])
        pm10 = _get(["pm10_corrected", "pm10"])
        pm1  = _get(["pm01_corrected", "pm01", "pm1"])
        co2  = _get(["rco2_corrected", "rco2", "co2"], default=400.0)
        temp = _get(["atmp_corrected", "atmp", "temperature"], default=25.0)
        hum  = _get(["rhum_corrected", "rhum", "humidity"], default=50.0)
        tvoc = _get(["tvoc"], default=0.0)
        nox  = _get(["noxIndex", "nox"], default=0.0)
        pm03 = _get(["pm003Count", "pm003_count"], default=0.0)

        # Horodatage
        ts = raw.get("timestamp") or raw.get("date") or datetime.utcnow().isoformat()

        # Calculs
        mesures_pour_iqa = {
            "pm02_corrected": pm25,
            "pm10_corrected": pm10,
            "rco2_corrected": co2,
            "tvoc":           tvoc,
            "noxIndex":       nox,
        }
        iqa = calculer_iqa(mesures_pour_iqa)
        aqi = compute_aqi_epa(pm25)

        return AirData(
            pm25=round(pm25, 1),
            pm10=round(pm10, 1),
            pm1=round(pm1, 1),
            co2=round(co2, 0),
            temperature=round(temp, 1),
            humidity=round(hum, 0),
            tvoc=round(tvoc, 1),
            nox=round(nox, 1),
            pm03_count=round(pm03, 0),
            aqi=aqi,
            iqa=iqa,
            aqi_level=get_aqi_level(aqi),
            last_updated=str(ts),
            source="airgradient",
        )
    except Exception as e:
        logger.warning(f"Erreur parsing mesure AirGradient : {e} | raw={raw}")
        return None

# ─── Client AirGradient ───────────────────────────────────────────────────────

def _ag_params(extra: Dict = None) -> Dict:
    """Paramètres de base pour toutes les requêtes AirGradient."""
    p = {"token": AG_TOKEN}
    if extra:
        p.update(extra)
    return p

async def ag_get(path: str, params: Dict = None) -> Optional[Any]:
    """Requête GET générique vers l'API AirGradient."""
    url = f"{AG_BASE_URL}{path}"
    all_params = _ag_params(params or {})
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=all_params)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"AirGradient GET {path} → HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"AirGradient GET {path} → Erreur: {e}")
    return None

async def fetch_current_measure(location_id: str) -> Optional[AirData]:
    """
    Récupère les mesures actuelles d'un capteur.
    Endpoint : GET /locations/{locationId}/measures/current
    """
    cache_key = f"current_{location_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    data = await ag_get(f"/locations/{location_id}/measures/current")
    if data is None:
        return None

    # L'API retourne soit un dict soit une liste d'un élément
    raw = data[0] if isinstance(data, list) and data else data
    if not isinstance(raw, dict):
        return None

    measure = parse_ag_measure(raw)
    if measure:
        cache_set(cache_key, measure)
    return measure

async def fetch_all_current_measures() -> Dict[str, AirData]:
    """
    Récupère les mesures de TOUTES les locations du compte en une seule requête.
    Endpoint : GET /locations/measures/current
    Plus efficace que N requêtes individuelles.
    """
    cache_key = "all_current"
    cached = cache_get(cache_key)
    if cached:
        return cached

    data = await ag_get("/locations/measures/current")
    if data is None:
        return {}

    result: Dict[str, AirData] = {}
    items = data if isinstance(data, list) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        loc_id = str(
            item.get("locationId")
            or item.get("location_id")
            or item.get("id")
            or ""
        )
        if not loc_id:
            continue
        measure = parse_ag_measure(item)
        if measure:
            result[loc_id] = measure

    logger.info(f"AirGradient /locations/measures/current → {len(result)} capteur(s) chargé(s)")
    cache_set("all_current", result)
    return result

async def fetch_past_measures(location_id: str, hours: int = 24) -> List[Dict]:
    """
    Récupère l'historique des mesures.
    Endpoint : GET /locations/{locationId}/measures/past
    """
    cache_key = f"past_{location_id}_{hours}h"
    cached = cache_get(cache_key)
    if cached:
        return cached

    now = datetime.utcnow()
    from_dt = now - timedelta(hours=hours)

    # Format identique à votre functions.py
    from_str = from_dt.strftime('%Y%m%dT%H%M%SZ')
    to_str   = now.strftime('%Y%m%dT%H%M%SZ')

    data = await ag_get(
        f"/locations/{location_id}/measures/past",
        params={"from": from_str, "to": to_str}
    )

    if not data or not isinstance(data, list):
        return []

    history = []
    for item in data:
        if not isinstance(item, dict):
            continue
        m = parse_ag_measure(item)
        if m:
            history.append({
                "timestamp":   m.last_updated,
                "aqi":         m.aqi,
                "iqa":         m.iqa,
                "pm25":        m.pm25,
                "pm10":        m.pm10,
                "co2":         m.co2,
                "temperature": m.temperature,
                "humidity":    m.humidity,
                "tvoc":        m.tvoc,
                "nox":         m.nox,
            })

    cache_set(cache_key, history)
    return history

async def fetch_raw_measures(location_id: str) -> List[Dict]:
    """
    Récupère les 200 mesures brutes les plus récentes.
    Endpoint : GET /locations/{locationId}/measures/raw
    """
    data = await ag_get(f"/locations/{location_id}/measures/raw")
    if not data or not isinstance(data, list):
        return []
    return data

# ─── Données mock (fallback si API indisponible) ──────────────────────────────

MOCK_DATA = {
    "1":  {"pm25":8.2,  "pm10":18.4,"co2":412,"temp":28.5,"hum":72,"tvoc":45, "nox":10},
    "2":  {"pm25":18.5, "pm10":32.1,"co2":580,"temp":30.1,"hum":68,"tvoc":82, "nox":22},
    "3":  {"pm25":35.4, "pm10":62.8,"co2":720,"temp":31.2,"hum":65,"tvoc":130,"nox":45},
    "4":  {"pm25":52.3, "pm10":88.7,"co2":890,"temp":32.0,"hum":60,"tvoc":180,"nox":65},
    "5":  {"pm25":23.6, "pm10":41.2,"co2":630,"temp":30.5,"hum":67,"tvoc":95, "nox":30},
    "6":  {"pm25":6.3,  "pm10":14.1,"co2":390,"temp":27.8,"hum":78,"tvoc":35, "nox":8},
    "7":  {"pm25":40.2, "pm10":71.5,"co2":760,"temp":31.5,"hum":63,"tvoc":150,"nox":55},
    "8":  {"pm25":10.1, "pm10":21.5,"co2":430,"temp":28.9,"hum":74,"tvoc":55, "nox":15},
    "9":  {"pm25":7.1,  "pm10":15.8,"co2":395,"temp":33.2,"hum":55,"tvoc":40, "nox":10},
    "10": {"pm25":15.3, "pm10":28.7,"co2":510,"temp":34.0,"hum":52,"tvoc":70, "nox":20},
    "11": {"pm25":20.5, "pm10":36.8,"co2":595,"temp":31.8,"hum":62,"tvoc":88, "nox":28},
    "12": {"pm25":21.2, "pm10":37.9,"co2":605,"temp":32.8,"hum":52,"tvoc":92, "nox":30},
    "13": {"pm25":5.6,  "pm10":12.3,"co2":380,"temp":29.5,"hum":82,"tvoc":30, "nox":7},
    "14": {"pm25":44.2, "pm10":78.5,"co2":815,"temp":35.0,"hum":48,"tvoc":165,"nox":60},
    "15": {"pm25":48.6, "pm10":83.1,"co2":855,"temp":38.0,"hum":38,"tvoc":175,"nox":65},
    "16": {"pm25":14.1, "pm10":26.8,"co2":488,"temp":30.2,"hum":70,"tvoc":65, "nox":18},
    "17": {"pm25":26.2, "pm10":46.5,"co2":655,"temp":34.8,"hum":45,"tvoc":105,"nox":35},
    "18": {"pm25":4.5,  "pm10":10.8,"co2":365,"temp":31.5,"hum":78,"tvoc":28, "nox":6},
    "19": {"pm25":33.5, "pm10":59.8,"co2":705,"temp":33.5,"hum":50,"tvoc":125,"nox":42},
    "20": {"pm25":8.8,  "pm10":18.9,"co2":415,"temp":30.2,"hum":76,"tvoc":48, "nox":12},
}

def get_mock_air_data(school_id: str) -> AirData:
    import random
    d = MOCK_DATA.get(school_id, MOCK_DATA["1"])
    v = lambda x: round(float(x) * random.uniform(0.93, 1.07), 1)

    pm25 = v(d["pm25"])
    pm10 = v(d["pm10"])
    co2  = round(v(d["co2"]))
    temp = round(float(d["temp"]) + random.uniform(-0.5, 0.5), 1)
    hum  = round(float(d["hum"]) + random.uniform(-2, 2), 0)
    tvoc = v(d.get("tvoc", 0))
    nox  = v(d.get("nox", 0))

    mesures = {
        "pm02_corrected": pm25,
        "pm10_corrected": pm10,
        "rco2_corrected": co2,
        "tvoc": tvoc,
        "noxIndex": nox,
    }
    iqa = calculer_iqa(mesures)
    aqi = compute_aqi_epa(pm25)

    return AirData(
        pm25=pm25, pm10=pm10, pm1=round(pm25 * 0.6, 1),
        co2=co2, temperature=temp, humidity=hum,
        tvoc=tvoc, nox=nox, pm03_count=0,
        aqi=aqi, iqa=iqa, aqi_level=get_aqi_level(aqi),
        last_updated=datetime.utcnow().isoformat(),
        source="mock",
    )

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "app": "RESPiRE API v3.0",
        "team": "Breath4Life — Hackathon KAIKAI 2025",
        "airgradient_token": "configuré" if AG_TOKEN else "manquant",
        "schools": len(SCHOOLS_CONFIG),
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
async def health():
    """Vérifie la connexion avec l'API AirGradient."""
    data = await ag_get("/ping")
    ag_ok = data is not None
    # Tenter aussi de récupérer les infos du compte
    place = await ag_get("/place")
    return {
        "status": "ok",
        "airgradient_ping": "ok" if ag_ok else "échec",
        "place": place,
        "mode": "live" if ag_ok else "mock",
        "cache_ttl": CACHE_TTL,
    }

@app.get("/schools/dropdown", response_model=List[dict])
def get_schools_dropdown():
    """
    Liste simplifiée des écoles pour le dropdown de l'alerte.
    Retourne uniquement id, name, city — sans données air (rapide).
    """
    return [
        {
            "id":      cfg["id"],
            "name":    cfg["name"],
            "city":    cfg["city"],
            "display": f"{cfg['name']} — {cfg['city']}",
        }
        for cfg in sorted(SCHOOLS_CONFIG, key=lambda x: (x["city"], x["name"]))
    ]

@app.get("/schools", response_model=List[School])
async def get_schools():
    """
    Retourne toutes les écoles avec leurs données air en temps réel.
    Stratégie :
      1. Récupère toutes les mesures en une requête (/locations/measures/current)
      2. Pour les écoles sans données, tente une requête individuelle
      3. Fallback mock si l'API est inaccessible
    """
    # Étape 1 : bulk fetch
    all_measures = await fetch_all_current_measures()

    schools = []
    for cfg in SCHOOLS_CONFIG:
        loc_id    = cfg["location_id"]
        school_id = cfg["id"]

        # Chercher dans le bulk
        air_data = all_measures.get(loc_id)

        # Étape 2 : requête individuelle si absent du bulk
        if air_data is None:
            air_data = await fetch_current_measure(loc_id)

        # Étape 3 : fallback mock
        if air_data is None:
            logger.info(f"Fallback mock pour école {school_id} ({cfg['name']})")
            air_data = get_mock_air_data(school_id)

        schools.append(School(
            id=school_id,
            name=cfg["name"],
            city=cfg["city"],
            lat=cfg["lat"],
            lng=cfg["lng"],
            aqi=air_data.aqi,
            iqa=air_data.iqa,
            air_data=air_data,
        ))

    # Tri par IQA décroissant (plus pollué en premier, comme votre classify_by_iqa)
    schools.sort(key=lambda s: s.iqa, reverse=True)
    return schools

@app.get("/schools/{school_id}/air", response_model=AirData)
async def get_school_air(school_id: str):
    """Données air en temps réel pour une école spécifique."""
    cfg = next((s for s in SCHOOLS_CONFIG if s["id"] == school_id), None)
    if not cfg:
        raise HTTPException(404, f"École '{school_id}' non trouvée")

    air_data = await fetch_current_measure(cfg["location_id"])
    if air_data is None:
        logger.info(f"Fallback mock pour école {school_id}")
        air_data = get_mock_air_data(school_id)

    return air_data

@app.get("/schools/{school_id}/history")
async def get_school_history(
    school_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Nombre d'heures"),
):
    """
    Historique des mesures d'une école.
    Endpoint AirGradient : /locations/{locationId}/measures/past
    """
    cfg = next((s for s in SCHOOLS_CONFIG if s["id"] == school_id), None)
    if not cfg:
        raise HTTPException(404, "École non trouvée")

    history = await fetch_past_measures(cfg["location_id"], hours)

    if not history:
        # Générer un historique mock réaliste
        history = _generate_mock_history(school_id, hours)

    return {
        "school_id":   school_id,
        "school_name": cfg["name"],
        "hours":       hours,
        "count":       len(history),
        "data":        history,
    }

@app.get("/schools/{school_id}/raw")
async def get_school_raw(school_id: str):
    """200 mesures brutes les plus récentes d'un capteur."""
    cfg = next((s for s in SCHOOLS_CONFIG if s["id"] == school_id), None)
    if not cfg:
        raise HTTPException(404, "École non trouvée")

    raw = await fetch_raw_measures(cfg["location_id"])
    return {"school_id": school_id, "count": len(raw), "data": raw}

@app.get("/alarms")
async def get_alarms():
    """Alarmes déclenchées sur toutes les locations."""
    data = await ag_get("/alarms/triggered")
    return {
        "alarms": data if data else [],
        "source": "airgradient" if data is not None else "none",
    }

@app.get("/place")
async def get_place():
    """Informations sur le compte AirGradient (place)."""
    data = await ag_get("/place")
    if not data:
        raise HTTPException(503, "Impossible de joindre l'API AirGradient")
    return data

@app.post("/alert")
async def send_alert(req: AlertRequest):
    """Envoie un email d'alerte pollution via Resend API (HTTP)."""
    logger.info(f"📨 Alerte reçue — école: {req.school}")
    logger.info(f"   RESEND_API_KEY: {'✅ configuré' if RESEND_API_KEY else '❌ VIDE'}")
    logger.info(f"   ALERT_EMAIL: {ALERT_EMAIL or '❌ VIDE'}")
    try:
        await _send_email_resend(req)
        logger.info("✅ Email envoyé avec succès")
        return {"success": True, "message": "Alerte envoyée avec succès"}
    except Exception as e:
        logger.error(f"❌ Erreur email : {type(e).__name__}: {e}")
        raise HTTPException(500, f"Erreur email: {str(e)}")

@app.get("/test-email")
async def test_email():
    """Diagnostic de la config email — ouvrir dans le navigateur."""
    config = {
        "RESEND_API_KEY": "✅ configuré" if RESEND_API_KEY else "❌ VIDE",
        "ALERT_EMAIL":    ALERT_EMAIL or "❌ VIDE",
        "ALERT_FROM":     ALERT_FROM,
        "SMTP_USER":      "✅ " + SMTP_USER[:3] + "***" if SMTP_USER else "❌ VIDE",
    }
    if not RESEND_API_KEY:
        return {
            "status": "❌ RESEND_API_KEY manquant",
            "config": config,
            "fix": "1) Créer un compte sur resend.com  2) Créer une API Key  3) Ajouter RESEND_API_KEY dans Railway Variables",
        }
    if not ALERT_EMAIL:
        return {
            "status": "❌ ALERT_EMAIL manquant",
            "config": config,
            "fix": "Ajouter ALERT_EMAIL dans Railway Variables (ex: tonmail@gmail.com)",
        }
    # Test d'envoi réel
    try:
        req_test = AlertRequest(
            school="Test RESPiRE",
            description="Ceci est un email de test automatique."
        )
        await _send_email_resend(req_test)
        return {"status": "✅ Email test envoyé avec succès", "to": ALERT_EMAIL, "config": config}
    except Exception as e:
        return {"status": f"❌ Échec: {type(e).__name__}: {str(e)}", "config": config}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_mock_history(school_id: str, hours: int) -> List[Dict]:
    import random
    base = MOCK_DATA.get(school_id, MOCK_DATA["1"])
    history = []
    now = datetime.utcnow()
    for i in range(hours):
        ts = now - timedelta(hours=hours - i)
        v  = lambda x: round(float(x) * random.uniform(0.85, 1.15), 1)
        pm25 = v(base["pm25"])
        co2  = round(v(base["co2"]))
        tvoc = v(base.get("tvoc", 50))
        nox  = v(base.get("nox", 20))
        iqa  = calculer_iqa({
            "pm02_corrected": pm25,
            "pm10_corrected": v(base["pm10"]),
            "rco2_corrected": co2,
            "tvoc": tvoc,
            "noxIndex": nox,
        })
        history.append({
            "timestamp":   ts.isoformat(),
            "aqi":         compute_aqi_epa(pm25),
            "iqa":         iqa,
            "pm25":        pm25,
            "pm10":        v(base["pm10"]),
            "co2":         co2,
            "temperature": round(float(base["temp"]) + random.uniform(-1.5, 1.5), 1),
            "humidity":    round(float(base["hum"])  + random.uniform(-5, 5), 0),
            "tvoc":        tvoc,
            "nox":         nox,
        })
    return history

async def _send_email_resend(req: AlertRequest) -> None:
    """Envoie un email via l'API HTTP Resend — fonctionne même si SMTP est bloqué."""
    has_photo = bool(req.photo_base64)
    now_str   = datetime.now().strftime('%d/%m/%Y à %H:%M')

    # Mode DEV : pas de clé → juste logger
    if not RESEND_API_KEY:
        logger.info(f"""
═══════════════════════════════════
📧 ALERTE RESPiRE [DEV — pas d'envoi réel]
École      : {req.school}
Description: {req.description}
Photo      : {'Oui' if has_photo else 'Non'}
Heure      : {now_str}
🔧 Pour activer : ajouter RESEND_API_KEY dans Railway Variables
═══════════════════════════════════""")
        return

    if not ALERT_EMAIL:
        raise ValueError("ALERT_EMAIL non configuré dans Railway Variables")

    # Corps HTML de l'email
    photo_html = ""
    if has_photo:
        photo_html = f"""
        <p style="margin-top:16px">
          <strong>📷 Photo :</strong> {req.photo_filename or 'photo.jpg'}<br>
          <em style="color:#666;font-size:12px">(image en pièce jointe)</em>
        </p>"""

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#FF5722;color:white;padding:20px;border-radius:10px 10px 0 0;">
        <h2 style="margin:0">🚨 Alerte Pollution — RESPiRE</h2>
      </div>
      <div style="padding:20px;background:#f9f9f9;border:1px solid #ddd;border-radius:0 0 4px 4px;">
        <p><strong>École :</strong> {req.school}</p>
        <p><strong>Date :</strong> {now_str}</p>
        <p><strong>Description :</strong></p>
        <blockquote style="border-left:4px solid #FF5722;padding-left:12px;margin:0;color:#333;">
          {req.description}
        </blockquote>
        {photo_html}
      </div>
      <div style="padding:12px;background:#00897B;color:white;border-radius:0 0 10px 10px;text-align:center;font-size:13px;">
        RESPiRE • Breath4Life • Hackathon KAIKAI 2025
      </div>
    </div>"""

    # Préparer attachments (photo en base64)
    attachments = []
    if has_photo and req.photo_base64:
        attachments.append({
            "filename": req.photo_filename or "photo.jpg",
            "content":  req.photo_base64,
        })

    # Appel API Resend (HTTP — pas SMTP)
    payload = {
        "from":        ALERT_FROM,
        "to":          [ALERT_EMAIL],
        "subject":     f"ALERTE POLLUTION Projet de Mesure de la Qualité de l'air",
        "html":        html_body,
    }
    if attachments:
        payload["attachments"] = attachments

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type":  "application/json",
            },
            json=payload,
        )

    if resp.status_code not in (200, 201):
        raise ValueError(f"Resend API error {resp.status_code}: {resp.text}")

    logger.info(f"📧 Email envoyé via Resend → {ALERT_EMAIL} (id: {resp.json().get('id', '?')})")

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)