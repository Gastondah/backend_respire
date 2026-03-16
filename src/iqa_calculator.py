import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# TODO: Move to config
VALEURS_LIMITE = {
    "pm02_corrected": 25,  # PM2.5 limit
    "rco2_corrected": 1000,  # CO2 limit
    "pm10_corrected": 50,  # PM10 limit
    "tvoc": 0.6,  # TVOC limit
    "noxIndex": 50,  # NOx limit
    "pm01_corrected": 15,  # PM1 limit
}

def calculer_iqa(data: Dict[str, Any]) -> float:
    """
    Calculate IQA (Air Quality Index) from air quality data.

    :param data: Dict with pollutant measurements
    :return: IQA value (0-100+)
    """
    try:
        iqa_values = {}

        # Calculate IQA for each pollutant
        for pollutant, limit in VALEURS_LIMITE.items():
            if pollutant in data:
                concentration = float(data[pollutant])
                if concentration > 0:
                    iqa_values[pollutant] = (concentration / limit) * 100

        if not iqa_values:
            logger.warning("No valid pollutants found for IQA calculation")
            return 0.0

        # Return the highest IQA (worst pollutant)
        return round(max(iqa_values.values()), 2)

    except Exception as e:
        logger.error(f"Error calculating IQA: {e}")
        return 0.0

def get_aqi_status(iqa: float) -> str:
    """
    Get air quality status from IQA value.

    :param iqa: IQA value
    :return: Status string
    """
    if iqa <= 50:
        return "Excellente"
    elif iqa <= 100:
        return "Bonne"
    elif iqa <= 150:
        return "Moyenne"
    elif iqa <= 200:
        return "Mauvaise"
    else:
        return "Très mauvaise"

def calculate_air_quality_status(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate detailed air quality status for parents.

    :param data: Air quality data dict
    :return: Dict with status, color, message, advice, and metrics
    """
    try:
        pm25 = float(data.get('pm25', 0))
        co2 = float(data.get('co2', 400))
        temp = float(data.get('temp', 25))
        humidity = float(data.get('humidity', 50))

        iqa = calculer_iqa(data)
        status = get_aqi_status(iqa)

        # Define status details
        if iqa <= 50:
            color = "#4caf50"
            icon = "😊"
            message = "L'air est pur ! Votre enfant respire dans de bonnes conditions."
            advice = "Parfait pour toutes les activités à l'école."
        elif iqa <= 100:
            color = "#8bc34a"
            icon = "🙂"
            message = "La qualité de l'air est satisfaisante."
            advice = "Conditions normales, rien à signaler."
        elif iqa <= 150:
            color = "#ff9800"
            icon = "😐"
            message = "L'air pourrait être mieux. Surveillez les symptômes chez votre enfant."
            advice = "Encouragez votre enfant à bien s'hydrater."
        elif iqa <= 200:
            color = "#f44336"
            icon = "😷"
            message = "Air pollué. Soyez vigilant aux signes de gêne respiratoire."
            advice = "Contactez l'école si votre enfant tousse ou a du mal à respirer."
        else:
            color = "#d32f2f"
            icon = "😨"
            message = "Air très pollué ! Surveillez attentivement votre enfant."
            advice = "Consultez un médecin si votre enfant présente des symptômes."

        return {
            "status": status,
            "color": color,
            "icon": icon,
            "message": message,
            "advice": advice,
            "iqa": round(iqa, 2),
            "pm25": pm25,
            "co2": co2,
            "temp": temp,
            "humidity": humidity,
            "last_update": data.get('last_update', 'Unknown')
        }

    except Exception as e:
        logger.error(f"Error calculating air quality status: {e}")
        return {
            "status": "Erreur",
            "color": "#666666",
            "icon": "❓",
            "message": "Erreur de calcul",
            "advice": "Vérifiez les données",
            "iqa": 0.0,
            "pm25": 0.0,
            "co2": 0.0,
            "temp": 0.0,
            "humidity": 0.0,
            "last_update": "Erreur"
        }

def classify_devices_by_iqa(devices_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Classify all devices by their IQA values.

    :param devices_data: Dict mapping device_id to data
    :return: Dict with classifications and summary
    """
    try:
        classifications = {}
        iqas = []

        for device_id, data in devices_data.items():
            iqa = calculer_iqa(data)
            status = get_aqi_status(iqa)
            classifications[device_id] = {
                "iqa": round(iqa, 2),
                "status": status,
                "data": data
            }
            iqas.append(iqa)

        # Summary statistics
        if iqas:
            summary = {
                "total_devices": len(iqas),
                "average_iqa": round(np.mean(iqas), 2),
                "max_iqa": round(max(iqas), 2),
                "min_iqa": round(min(iqas), 2),
                "worst_device": max(classifications.items(), key=lambda x: x[1]["iqa"])[0]
            }
        else:
            summary = {"total_devices": 0}

        return {
            "classifications": classifications,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error classifying devices by IQA: {e}")
        return {"classifications": {}, "summary": {"error": str(e)}}
