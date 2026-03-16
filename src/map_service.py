import folium
from folium import plugins
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

def get_air_quality_color(status: str) -> str:
    """Return background color for air quality status"""
    color_map = {
        "excellente": "#1b5e20",
        "bonne": "#f9a825",
        "moyenne": "#ef6c00",
        "mauvaise": "#c62828",
        "très mauvaise": "#6a1b9a"
    }
    return color_map.get(status.lower(), "#37474f")

def get_air_quality_icon(status: str) -> str:
    """Return emoji icon for air quality status"""
    icon_map = {
        "excellente": "😊",
        "bonne": "🙂",
        "moyenne": "😐",
        "mauvaise": "😷",
        "très mauvaise": "🚨"
    }
    return icon_map.get(status.lower(), "❓")

def create_styled_popup(location_data: Dict[str, Any]) -> str:
    """Create styled HTML popup for map marker"""
    try:
        name = location_data.get('name', 'Unknown')
        status = location_data.get('status', 'Unknown').lower()
        data = location_data.get('data', {})

        bg_color = get_air_quality_color(status)
        icon = get_air_quality_icon(status)

        # Build metrics HTML
        metrics = [
            ("⏰", "Dernière MAJ", data.get('last_update', 'N/A')),
            ("🌫️", "PM2.5", f"{data.get('pm25', 0):.1f} µg/m³"),
            ("💨", "CO₂", f"{data.get('co2', 400):.0f} ppm"),
            ("🌡️", "Température", f"{data.get('temp', 25):.1f} °C"),
            ("💧", "Humidité", f"{data.get('humidity', 50):.1f} %"),
            ("🏭", "PM10", f"{data.get('pm10', 0):.1f} µg/m³"),
            ("🌫️", "PM1", f"{data.get('pm1', 0):.1f} µg/m³"),
            ("🔬", "PM0.3", f"{data.get('pm03', 0)}"),
            ("🧴", "TVOC", f"{data.get('tvoc', 0):.1f}"),
            ("🚗", "NOx", f"{data.get('nox', 0):.1f}")
        ]

        metrics_html = ""
        for icon_metric, label, value in metrics:
            metrics_html += f"""
            <div style="display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <span style="font-size: 16px; margin-right: 10px; width: 25px;">{icon_metric}</span>
                <span style="flex: 1; font-size: 13px; opacity: 0.9;">{label}</span>
                <span style="font-weight: 600; font-size: 13px;">{value}</span>
            </div>
            """

        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; width: 340px; background: linear-gradient(135deg, {bg_color}dd, {bg_color}aa); backdrop-filter: blur(10px); border-radius: 20px; padding: 0; box-shadow: 0 20px 40px rgba(0,0,0,0.2); overflow: hidden; color: white; border: 1px solid rgba(255,255,255,0.2);">
            <div style="background: rgba(255,255,255,0.1); padding: 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.2);">
                <div style="font-size: 30px; margin-bottom: 5px;">{icon}</div>
                <h3 style="margin: 0; font-size: 18px; font-weight: 600;">{name}</h3>
                <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px;">Qualité: {status.title()}</p>
            </div>
            <div style="padding: 15px 20px; max-height: 250px; overflow-y: auto;">
                {metrics_html}
            </div>
            <div style="background: rgba(0,0,0,0.2); padding: 10px 20px; text-align: center; font-size: 11px; opacity: 0.8;">
                📡 Données recueillies en temps réel
            </div>
        </div>
        """

        return popup_html

    except Exception as e:
        logger.error(f"Error creating popup: {e}")
        return f"<div>Error creating popup: {e}</div>"

def create_map_html(locations_data: List[Dict[str, Any]], center_lat: float = 14.5, center_lon: float = -14.5, zoom: int = 6) -> str:
    """
    Create interactive map HTML with school locations and air quality data.

    :param locations_data: List of dicts with location info and air quality data
    :param center_lat: Map center latitude
    :param center_lon: Map center longitude
    :param zoom: Initial zoom level
    :return: HTML string of the map
    """
    try:
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles=None
        )

        # Add tile layers
        folium.TileLayer('CartoDB Positron', name='Clair', control=True).add_to(m)
        folium.TileLayer('CartoDB Dark_Matter', name='Sombre', control=True).add_to(m)
        folium.TileLayer('OpenStreetMap', name='Standard', control=True).add_to(m)

        # Add markers
        marker_cluster = plugins.MarkerCluster(name="Capteurs").add_to(m)

        for loc in locations_data:
            try:
                lat = loc.get('lat')
                lon = loc.get('lon')

                if lat is None or lon is None:
                    logger.warning(f"Missing coordinates for location: {loc.get('name', 'Unknown')}")
                    continue

                # Create popup
                popup_html = create_styled_popup(loc)

                # Create marker
                marker = folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=400),
                    tooltip=f"<b>{loc.get('name', 'Unknown')}</b><br>Qualité: {loc.get('status', 'Unknown')}",
                    icon=folium.Icon(
                        color=get_marker_color(loc.get('status', 'Unknown')),
                        icon='cloud'  # Default icon
                    )
                )

                marker.add_to(marker_cluster)

            except Exception as e:
                logger.error(f"Error adding marker for location {loc.get('name', 'Unknown')}: {e}")
                continue

        # Add legend
        legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; width: 200px; height: auto; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border-radius: 15px; padding: 15px; font-size: 12px; font-family: 'Segoe UI', sans-serif; box-shadow: 0 8px 32px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.2); z-index: 9999;">
            <h4 style="margin: 0 0 10px 0; color: #333;">Qualité de l'air</h4>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #00e400; border-radius: 50%; margin-right: 8px;"></div><span> Excellente</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #ffff00; border-radius: 50%; margin-right: 8px;"></div><span> Bonne</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #ff7e00; border-radius: 50%; margin-right: 8px;"></div><span> Moyenne</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #ff0000; border-radius: 50%; margin-right: 8px;"></div><span> Mauvaise</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #8f3f97; border-radius: 50%; margin-right: 8px;"></div><span> Très mauvaise</span></div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        # Add controls
        folium.LayerControl().add_to(m)
        plugins.LocateControl().add_to(m)

        # Generate HTML
        return m.get_root().render()

    except Exception as e:
        logger.error(f"Error creating map: {e}")
        return f"<div>Error creating map: {e}</div>"

def get_marker_color(status: str) -> str:
    """Get folium marker color from status"""
    color_map = {
        "excellente": "green",
        "bonne": "lightgreen",
        "moyenne": "orange",
        "mauvaise": "red",
        "très mauvaise": "darkred"
    }
    return color_map.get(status.lower(), "gray")

def create_map_with_selected_school(locations_data: List[Dict[str, Any]], selected_school: str) -> str:
    """
    Create map centered on selected school with enhanced marker.

    :param locations_data: List of location data
    :param selected_school: Name of selected school
    :return: HTML string of the map
    """
    try:
        # Find selected school
        selected_loc = None
        for loc in locations_data:
            if loc.get('name') == selected_school:
                selected_loc = loc
                break

        if selected_loc:
            center_lat = selected_loc.get('lat', 14.5)
            center_lon = selected_loc.get('lon', -14.5)
            zoom = 12
        else:
            center_lat, center_lon, zoom = 14.5, -14.5, 6

        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles=None
        )

        # Add tiles
        folium.TileLayer('CartoDB Positron', name='Clair', control=True).add_to(m)
        folium.TileLayer('CartoDB Dark_Matter', name='Sombre', control=True).add_to(m)
        folium.TileLayer('OpenStreetMap', name='Standard', control=True).add_to(m)

        marker_cluster = plugins.MarkerCluster(name="Capteurs").add_to(m)

        for loc in locations_data:
            lat = loc.get('lat')
            lon = loc.get('lon')

            if lat is None or lon is None:
                continue

            popup_html = create_styled_popup(loc)

            if loc.get('name') == selected_school:
                # Enhanced marker for selected school
                selected_icon = folium.DivIcon(
                    html=f'''
                    <div style="transform: translate(-25px, -25px);">
                        <svg width="50" height="50" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="25" cy="25" r="23" fill="{get_air_quality_color(loc.get('status', 'Unknown'))}" stroke="white" stroke-width="4" opacity="0.9">
                                <animate attributeName="r" values="20;25;20" dur="2s" repeatCount="indefinite"/>
                            </circle>
                            <circle cx="25" cy="25" r="18" fill="{get_air_quality_color(loc.get('status', 'Unknown'))}" opacity="0.8"/>
                            <text x="25" y="30" text-anchor="middle" font-size="14" fill="white">{get_air_quality_icon(loc.get('status', 'Unknown'))}</text>
                        </svg>
                    </div>
                    ''',
                    icon_size=(50, 50),
                    icon_anchor=(25, 25)
                )
                icon = selected_icon
            else:
                icon = folium.Icon(
                    color=get_marker_color(loc.get('status', 'Unknown')),
                    icon='cloud'
                )

            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"<b>{loc.get('name', 'Unknown')}</b><br>Qualité: {loc.get('status', 'Unknown')}",
                icon=icon
            )
            marker.add_to(marker_cluster)

        # Add controls and legend
        folium.LayerControl().add_to(m)
        plugins.LocateControl().add_to(m)

        legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; width: 200px; height: auto; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border-radius: 15px; padding: 15px; font-size: 12px; font-family: 'Segoe UI', sans-serif; box-shadow: 0 8px 32px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.2); z-index: 9999;">
            <h4 style="margin: 0 0 10px 0; color: #333;">Qualité de l'air</h4>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #00e400; border-radius: 50%; margin-right: 8px;"></div><span> Excellente</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #ffff00; border-radius: 50%; margin-right: 8px;"></div><span> Bonne</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #ff7e00; border-radius: 50%; margin-right: 8px;"></div><span> Moyenne</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #ff0000; border-radius: 50%; margin-right: 8px;"></div><span> Mauvaise</span></div>
            <div style="display: flex; align-items: center; margin: 5px 0;"><div style="width: 15px; height: 15px; background: #8f3f97; border-radius: 50%; margin-right: 8px;"></div><span> Très mauvaise</span></div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        return m.get_root().render()

    except Exception as e:
        logger.error(f"Error creating map with selected school: {e}")
        return f"<div>Error creating map: {e}</div>"
