import requests
from urllib.parse import urlencode
from datetime import datetime
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# TODO: Move to config
BASE_URL = "https://api.airgradient.com/public/api/v1"
TOKEN = "your_airgradient_token_here"  # TODO: Load from .env

def fetch_current_data(location_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch current air quality data from AirGradient API.

    :param location_id: Device location ID
    :param token: API token (optional, uses default if not provided)
    :return: Dict with air quality data or None if error
    """
    if not token:
        token = TOKEN

    endpoint = f"/locations/{location_id}/measures/current"
    params = {"token": token}
    full_url = f"{BASE_URL}{endpoint}?{urlencode(params)}"

    try:
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "measures" in data:
            df_data = data["measures"]
        elif isinstance(data, dict):
            df_data = data
        else:
            logger.warning(f"Unexpected data format for {location_id}")
            return None

        # Extract and normalize data
        pm25 = df_data.get('pm02_corrected', 0) or 0
        co2 = df_data.get('rco2_corrected', 400) or 400
        temp = df_data.get('atmp_corrected', 25) or 25
        humidity = df_data.get('rhum_corrected', 50) or 50
        pm10 = df_data.get('pm10_corrected', 0) or 0
        pm1 = df_data.get('pm01_corrected', 0) or 0
        pm03 = df_data.get('pm003Count', 0) or 0
        tvoc = df_data.get('tvoc', 0) or 0
        nox = df_data.get('noxIndex', 0) or 0

        return {
            "pm25": float(pm25),
            "co2": float(co2),
            "temp": float(temp),
            "humidity": float(humidity),
            "pm10": float(pm10),
            "pm1": float(pm1),
            "pm03": int(pm03),
            "tvoc": float(tvoc),
            "nox": float(nox),
            "last_update": datetime.now().strftime("%H:%M"),
            "location_id": location_id
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching data for {location_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing data for {location_id}: {e}")
        return None

def get_past_measures(location_id: int, token: Optional[str] = None, days: int = 7) -> Optional[list]:
    """
    Get historical measures for a location.

    :param location_id: Device location ID
    :param token: API token
    :param days: Number of days to look back
    :return: List of historical data points
    """
    if not token:
        token = TOKEN

    from_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    to_date = from_date.replace(hour=23, minute=59, second=59)

    url = f"{BASE_URL}/locations/{location_id}/measures/past"
    params = {
        "token": token,
        "from": from_date.strftime('%Y%m%dT%H%M%SZ'),
        "to": to_date.strftime('%Y%m%dT%H%M%SZ'),
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            return data
        else:
            logger.warning(f"Unexpected historical data format for {location_id}")
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching historical data for {location_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error processing historical data for {location_id}: {e}")
        return []

def get_all_devices_data(device_ids: list, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch current data for all devices.

    :param device_ids: List of device IDs
    :param token: API token
    :return: Dict mapping device_id to data
    """
    results = {}
    for device_id in device_ids:
        data = fetch_current_data(device_id, token)
        if data:
            results[device_id] = data

    return results
