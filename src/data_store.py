import json
import os
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DataStore:
    """Data storage service for air quality data"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def save_device_data(self, device_id: str, data: Dict[str, Any]) -> bool:
        """
        Save current air quality data for a device.

        :param device_id: Device identifier
        :param data: Air quality data dict
        :return: Success status
        """
        try:
            # Create device-specific directory
            device_dir = os.path.join(self.data_dir, device_id)
            os.makedirs(device_dir, exist_ok=True)

            # Save latest data
            latest_file = os.path.join(device_dir, "latest.json")
            data_with_timestamp = {
                **data,
                "timestamp": datetime.now().isoformat(),
                "device_id": device_id
            }

            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(data_with_timestamp, f, indent=2, ensure_ascii=False)

            # Append to historical data
            self._append_historical_data(device_id, data_with_timestamp)

            return True

        except Exception as e:
            logger.error(f"Error saving data for device {device_id}: {e}")
            return False

    def load_device_data(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Load latest data for a device.

        :param device_id: Device identifier
        :return: Latest data dict or None
        """
        try:
            latest_file = os.path.join(self.data_dir, device_id, "latest.json")
            if os.path.exists(latest_file):
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading data for device {device_id}: {e}")
            return None

    def _append_historical_data(self, device_id: str, data: Dict[str, Any]) -> None:
        """
        Append data to historical CSV file.

        :param device_id: Device identifier
        :param data: Data to append
        """
        try:
            device_dir = os.path.join(self.data_dir, device_id)
            history_file = os.path.join(device_dir, "history.csv")

            # Prepare data for CSV
            csv_data = {
                "timestamp": data["timestamp"],
                "device_id": device_id,
                **{k: v for k, v in data.items() if k not in ["timestamp", "device_id"]}
            }

            df = pd.DataFrame([csv_data])

            # Append to existing file or create new
            if os.path.exists(history_file):
                existing_df = pd.read_csv(history_file)
                df = pd.concat([existing_df, df], ignore_index=True)

            df.to_csv(history_file, index=False)

        except Exception as e:
            logger.error(f"Error appending historical data for {device_id}: {e}")

    def get_historical_data(self, device_id: str, days: int = 7) -> Optional[pd.DataFrame]:
        """
        Get historical data for a device.

        :param device_id: Device identifier
        :param days: Number of days to look back
        :return: DataFrame with historical data
        """
        try:
            history_file = os.path.join(self.data_dir, device_id, "history.csv")
            if not os.path.exists(history_file):
                return None

            df = pd.read_csv(history_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df['timestamp'] >= cutoff_date]

            return df

        except Exception as e:
            logger.error(f"Error getting historical data for {device_id}: {e}")
            return None

    def save_bulk_data(self, devices_data: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Save data for multiple devices.

        :param devices_data: Dict mapping device_id to data
        :return: Dict with success status for each device
        """
        results = {}
        for device_id, data in devices_data.items():
            results[device_id] = self.save_device_data(device_id, data)
        return results

    def load_all_devices_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load latest data for all devices.

        :return: Dict mapping device_id to latest data
        """
        try:
            all_data = {}
            if os.path.exists(self.data_dir):
                for device_dir in os.listdir(self.data_dir):
                    device_path = os.path.join(self.data_dir, device_dir)
                    if os.path.isdir(device_path):
                        data = self.load_device_data(device_dir)
                        if data:
                            all_data[device_dir] = data
            return all_data
        except Exception as e:
            logger.error(f"Error loading all devices data: {e}")
            return {}

    def get_devices_list(self) -> List[str]:
        """
        Get list of all device IDs.

        :return: List of device IDs
        """
        try:
            devices = []
            if os.path.exists(self.data_dir):
                for item in os.listdir(self.data_dir):
                    device_path = os.path.join(self.data_dir, item)
                    if os.path.isdir(device_path):
                        devices.append(item)
            return devices
        except Exception as e:
            logger.error(f"Error getting devices list: {e}")
            return []

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old historical data.

        :param days_to_keep: Number of days of data to keep
        :return: Number of files cleaned
        """
        try:
            cleaned_count = 0
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            for device_id in self.get_devices_list():
                history_file = os.path.join(self.data_dir, device_id, "history.csv")
                if os.path.exists(history_file):
                    df = pd.read_csv(history_file)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df_filtered = df[df['timestamp'] >= cutoff_date]

                    if len(df_filtered) < len(df):
                        df_filtered.to_csv(history_file, index=False)
                        cleaned_count += 1
                        logger.info(f"Cleaned {len(df) - len(df_filtered)} old records for {device_id}")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning old data: {e}")
            return 0

    def export_data(self, device_id: str, format: str = "csv") -> Optional[str]:
        """
        Export device data in specified format.

        :param device_id: Device identifier
        :param format: Export format ("csv" or "json")
        :return: File path of exported data
        """
        try:
            data = self.load_device_data(device_id)
            history = self.get_historical_data(device_id)

            if not data and history is None:
                return None

            export_dir = os.path.join(self.data_dir, "exports")
            os.makedirs(export_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{device_id}_export_{timestamp}.{format}"
            filepath = os.path.join(export_dir, filename)

            if format == "json":
                export_data = {
                    "device_id": device_id,
                    "latest": data,
                    "historical": history.to_dict('records') if history is not None else []
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            elif format == "csv":
                if history is not None:
                    history.to_csv(filepath, index=False)
                else:
                    # Create CSV with latest data only
                    df = pd.DataFrame([data])
                    df.to_csv(filepath, index=False)

            return filepath

        except Exception as e:
            logger.error(f"Error exporting data for {device_id}: {e}")
            return None

# Convenience functions
def save_data(device_id: str, data: Dict[str, Any]) -> bool:
    """Save device data"""
    store = DataStore()
    return store.save_device_data(device_id, data)

def load_data(device_id: str) -> Optional[Dict[str, Any]]:
    """Load device data"""
    store = DataStore()
    return store.load_device_data(device_id)
