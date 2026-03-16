import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def get_sensibilisation_content() -> Dict[str, Any]:
    """
    Get sensibilisation content for air quality education.

    Returns structured content about air quality, pollutants, and health impacts.
    """
    try:
        content = {
            "introduction": {
                "title": "Comprendre la Qualité de l'Air",
                "content": "L'air que nous respirons contient différents polluants qui peuvent affecter notre santé. Il est important de comprendre ces polluants et leurs impacts pour mieux protéger notre santé.",
                "image": "assets/images/air_quality_intro.jpg"
            },
            "pollutants": {
                "title": "Les Principaux Polluants",
                "items": [
                    {
                        "name": "PM2.5",
                        "description": "Particules fines de moins de 2.5 micromètres",
                        "sources": ["Véhicules", "Industries", "Chauffage"],
                        "health_impacts": ["Problèmes respiratoires", "Maladies cardiovasculaires"],
                        "limit": "25 µg/m³ (moyenne annuelle OMS)"
                    },
                    {
                        "name": "PM10",
                        "description": "Particules de moins de 10 micromètres",
                        "sources": ["Poussière", "Construction", "Véhicules"],
                        "health_impacts": ["Irritation des voies respiratoires", "Asthme"],
                        "limit": "50 µg/m³ (moyenne annuelle OMS)"
                    },
                    {
                        "name": "CO₂",
                        "description": "Dioxyde de carbone",
                        "sources": ["Respiration", "Combustion", "Transports"],
                        "health_impacts": ["Fatigue", "Maux de tête", "Réduction des capacités cognitives"],
                        "limit": "1000 ppm (intérieur)"
                    },
                    {
                        "name": "TVOC",
                        "description": "Composés Organiques Volatils",
                        "sources": ["Peintures", "Colles", "Produits ménagers"],
                        "health_impacts": ["Irritation des yeux", "Maux de tête", "Problèmes respiratoires"],
                        "limit": "0.6 ppm"
                    },
                    {
                        "name": "NOx",
                        "description": "Oxydes d'azote",
                        "sources": ["Véhicules diesel", "Chauffage", "Industries"],
                        "health_impacts": ["Irritation pulmonaire", "Asthme"],
                        "limit": "50 µg/m³"
                    }
                ]
            },
            "iqa_scale": {
                "title": "L'Échelle IQA (Indice de Qualité de l'Air)",
                "description": "L'IQA est une échelle standardisée qui classe la qualité de l'air de 0 à 200+.",
                "levels": [
                    {
                        "range": "0-50",
                        "status": "Excellente",
                        "color": "#4CAF50",
                        "description": "Air pur, pas de risque pour la santé"
                    },
                    {
                        "range": "51-100",
                        "status": "Bonne",
                        "color": "#8BC34A",
                        "description": "Qualité d'air acceptable"
                    },
                    {
                        "range": "101-150",
                        "status": "Moyenne",
                        "color": "#FFC107",
                        "description": "Groupe sensibles peuvent ressentir des effets"
                    },
                    {
                        "range": "151-200",
                        "status": "Mauvaise",
                        "color": "#FF5722",
                        "description": "Risque pour la santé, réduire les activités extérieures"
                    },
                    {
                        "range": "200+",
                        "status": "Très mauvaise",
                        "color": "#F44336",
                        "description": "Risque élevé, éviter toute activité extérieure"
                    }
                ]
            },
            "health_impacts": {
                "title": "Impacts sur la Santé",
                "children": {
                    "title": "Chez les Enfants",
                    "impacts": [
                        "Développement pulmonaire affecté",
                        "Augmentation des allergies",
                        "Problèmes de concentration",
                        "Risque d'asthme plus élevé",
                        "Fatigue et maux de tête"
                    ]
                },
                "vulnerable_groups": {
                    "title": "Groupes Vulnérables",
                    "groups": [
                        "Personnes âgées",
                        "Femmes enceintes",
                        "Personnes avec maladies respiratoires",
                        "Enfants de moins de 12 ans"
                    ]
                }
            },
            "prevention": {
                "title": "Prévention et Protection",
                "tips": [
                    {
                        "category": "À l'école",
                        "actions": [
                            "Aérer les salles de classe régulièrement",
                            "Utiliser des plantes dépolluantes",
                            "Éviter les produits chimiques",
                            "Surveiller la qualité d'air"
                        ]
                    },
                    {
                        "category": "À la maison",
                        "actions": [
                            "Utiliser des purificateurs d'air",
                            "Bien ventiler lors des repas",
                            "Éviter de fumer à l'intérieur",
                            "Utiliser des produits naturels"
                        ]
                    },
                    {
                        "category": "Activités extérieures",
                        "actions": [
                            "Éviter les heures de forte pollution",
                            "Porter un masque en cas de pic",
                            "Pratiquer le sport tôt le matin",
                            "Surveiller les bulletins météo"
                        ]
                    }
                ]
            },
            "actions": {
                "title": "Actions Collectives",
                "initiatives": [
                    {
                        "title": "Programme RESPiRE",
                        "description": "Surveillance continue de la qualité de l'air dans les écoles"
                    },
                    {
                        "title": "Sensibilisation",
                        "description": "Éducation sur la qualité de l'air auprès des communautés scolaires"
                    },
                    {
                        "title": "Mesures Préventives",
                        "description": "Mise en place de solutions pour améliorer l'air intérieur"
                    }
                ]
            },
            "resources": {
                "title": "Ressources Utiles",
                "links": [
                    {
                        "title": "OMS - Qualité de l'Air",
                        "url": "https://www.who.int/health-topics/air-pollution"
                    },
                    {
                        "title": "AirGradient",
                        "url": "https://www.airgradient.com/"
                    },
                    {
                        "title": "Ministère de l'Environnement Sénégal",
                        "url": "https://www.environnement.gouv.sn/"
                    }
                ]
            },
            "quiz": {
                "title": "Testez vos Connaissances",
                "questions": [
                    {
                        "question": "Quelle est la taille maximale des particules PM2.5 ?",
                        "options": ["2.5 mm", "2.5 cm", "2.5 micromètres", "2.5 nanomètres"],
                        "correct": 2,
                        "explanation": "PM2.5 désigne les particules de moins de 2.5 micromètres (microns)"
                    },
                    {
                        "question": "Quel polluant peut causer des maux de tête et de la fatigue en intérieur ?",
                        "options": ["PM2.5", "CO₂", "PM10", "NOx"],
                        "correct": 1,
                        "explanation": "Le CO₂ en concentration élevée peut causer fatigue, maux de tête et réduire les capacités cognitives"
                    },
                    {
                        "question": "Quelle est la qualité d'air quand l'IQA est entre 0 et 50 ?",
                        "options": ["Mauvaise", "Excellente", "Très mauvaise", "Moyenne"],
                        "correct": 1,
                        "explanation": "Un IQA entre 0 et 50 correspond à une qualité d'air excellente"
                    }
                ]
            }
        }

        return content

    except Exception as e:
        logger.error(f"Error getting sensibilisation content: {e}")
        return {
            "error": "Unable to load sensibilisation content",
            "timestamp": datetime.now().isoformat()
        }

def get_pollutant_info(pollutant: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific pollutant.

    :param pollutant: Name of the pollutant (PM25, CO2, etc.)
    :return: Dict with pollutant information or None if not found
    """
    try:
        content = get_sensibilisation_content()
        pollutants = content.get('pollutants', {}).get('items', [])

        for p in pollutants:
            if p['name'].lower() == pollutant.lower():
                return p

        return None

    except Exception as e:
        logger.error(f"Error getting pollutant info for {pollutant}: {e}")
        return None

def get_iqa_info(iqa_value: float) -> Optional[Dict[str, Any]]:
    """
    Get information about air quality level for a given IQA value.

    :param iqa_value: IQA value
    :return: Dict with IQA level information
    """
    try:
        content = get_sensibilisation_content()
        levels = content.get('iqa_scale', {}).get('levels', [])

        for level in levels:
            range_parts = level['range'].split('-')
            if len(range_parts) == 2:
                min_val = int(range_parts[0])
                max_val = int(range_parts[1]) if range_parts[1] != '+' else float('inf')

                if min_val <= iqa_value < max_val:
                    return level
            elif range_parts[0] == '200+':
                if iqa_value >= 200:
                    return level

        return None

    except Exception as e:
        logger.error(f"Error getting IQA info for value {iqa_value}: {e}")
        return None

def get_health_tips(iqa_level: str) -> List[str]:
    """
    Get health tips based on air quality level.

    :param iqa_level: Air quality level (excellente, bonne, etc.)
    :return: List of health tips
    """
    tips_map = {
        "excellente": [
            "Profitez des activités extérieures !",
            "L'air est pur et sain"
        ],
        "bonne": [
            "Qualité d'air acceptable",
            "Activités normales recommandées"
        ],
        "moyenne": [
            "Surveillez les symptômes chez les enfants sensibles",
            "Hydratez-vous régulièrement",
            "Évitez les efforts physiques intenses"
        ],
        "mauvaise": [
            "Réduisez les activités extérieures",
            "Portez un masque si nécessaire",
            "Fermez les fenêtres si pollution extérieure"
        ],
        "très mauvaise": [
            "Restez à l'intérieur autant que possible",
            "Utilisez un purificateur d'air",
            "Consultez un médecin en cas de symptômes",
            "Évitez tout effort physique"
        ]
    }

    return tips_map.get(iqa_level.lower(), ["Surveillez la qualité de l'air"])
