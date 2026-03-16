import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from src.models import AlertRequest

logger = logging.getLogger(__name__)

class AlertService:
    """Unified alert service for SMS and WhatsApp notifications"""

    def __init__(self, contacts_file: str = "parents_contacts.txt", config_file: str = "alert_config.json"):
        self.contacts_file = contacts_file
        self.config_file = config_file
        self.sent_alerts_file = "sent_alerts.json"

        # Default config
        self.config = {
            "enabled": True,
            "max_alerts_per_day": 5,
            "max_alerts_per_hour": 2,
            "quiet_hours_start": "21:00",
            "quiet_hours_end": "07:00",
            "pm25_alert_threshold": 35,
            "pm25_danger_threshold": 150,
            "co2_alert_threshold": 1000,
            "sms_provider": "twilio",  # "twilio" or "wachap"
            "wachap_base_url": "https://wachap.app/api",
            "wachap_access_token": os.getenv("WACHAP_ACCESS_TOKEN", ""),
            "wachap_instance_id": os.getenv("WACHAP_INSTANCE_ID", ""),
            "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
            "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
            "twilio_phone_number": os.getenv("TWILIO_PHONE_NUMBER", "")
        }

        self.load_config()
        self.load_sent_alerts()

    def load_config(self):
        """Load alert configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            else:
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def save_config(self):
        """Save alert configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def load_sent_alerts(self):
        """Load sent alerts history"""
        try:
            if os.path.exists(self.sent_alerts_file):
                with open(self.sent_alerts_file, 'r', encoding='utf-8') as f:
                    self.sent_alerts = json.load(f)
            else:
                self.sent_alerts = {}
                self.save_sent_alerts()
        except Exception as e:
            logger.error(f"Error loading sent alerts: {e}")
            self.sent_alerts = {}

    def save_sent_alerts(self):
        """Save sent alerts history"""
        try:
            with open(self.sent_alerts_file, 'w', encoding='utf-8') as f:
                json.dump(self.sent_alerts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving sent alerts: {e}")

    def load_contacts(self) -> List[Dict]:
        """Load parent contacts"""
        contacts = []
        try:
            if os.path.exists(self.contacts_file):
                with open(self.contacts_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 4:
                                phone = self._normalize_phone(parts[1])
                                if phone:
                                    contacts.append({
                                        'name': parts[0],
                                        'phone': phone,
                                        'child': parts[2],
                                        'class': parts[3]
                                    })
        except Exception as e:
            logger.error(f"Error loading contacts: {e}")
        return contacts

    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number"""
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) == 9 and digits[0] in ('7', '3'):
            return f"+221{digits}"
        return None

    def is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours"""
        now = datetime.now().time()
        start = datetime.strptime(self.config['quiet_hours_start'], '%H:%M').time()
        end = datetime.strptime(self.config['quiet_hours_end'], '%H:%M').time()

        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end

    def can_send_alert(self, alert_type: str, phone: str) -> Tuple[bool, str]:
        """Check if alert can be sent"""
        if not self.config.get('enabled', True):
            return False, "Service disabled"

        if self.is_quiet_hours():
            return False, "Quiet hours"

        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        hour_key = now.strftime('%Y-%m-%d-%H')

        # Daily limit
        daily_key = f"{phone}_{alert_type}_{today}"
        if daily_key in self.sent_alerts:
            return False, "Already sent today"

        # Daily count limit
        daily_count = sum(1 for k in self.sent_alerts.keys()
                         if k.startswith(f"{phone}_") and k.endswith(f"_{today}"))
        if daily_count >= self.config['max_alerts_per_day']:
            return False, "Daily limit reached"

        # Hourly limit
        hourly_count = sum(1 for k, v in self.sent_alerts.items()
                          if k.startswith(f"{phone}_") and
                          v.get('timestamp', '').startswith(hour_key))
        if hourly_count >= self.config['max_alerts_per_hour']:
            return False, "Hourly limit reached"

        return True, "OK"

    def generate_alert_message(self, alert_type: str, air_data: Dict, school_name: str, child_name: str) -> str:
        """Generate alert message"""
        pm25 = air_data.get('pm25', 0)
        co2 = air_data.get('co2', 400)
        timestamp = datetime.now().strftime('%H:%M')

        messages = {
            'pollution_high': f"🚨 {school_name}\nAir très pollué pour {child_name}\nPM2.5: {pm25:.1f} µg/m³\nHydratation recommandée\n⏰ {timestamp}",
            'pollution_moderate': f"⚠️ {school_name}\nAir dégradé - {child_name}\nPM2.5: {pm25:.1f} µg/m³\nSurveillez l'état au retour\n⏰ {timestamp}",
            'co2_high': f"💨 {school_name}\nCO₂ élevé classe de {child_name}\n{co2:.0f} ppm\nPossible fatigue\nÉcole informée\n⏰ {timestamp}",
            'back_to_normal': f"✅ {school_name}\nAir redevenu bon pour {child_name}\nActivités normales OK\n⏰ {timestamp}",
            'daily_report': f"📊 {school_name}\n{child_name}: Air {air_data.get('status', 'Unknown')}\nPM2.5: {pm25:.1f} µg/m³\n⏰ {timestamp}"
        }

        return messages.get(alert_type, f"Alerte {school_name}: {air_data.get('status', 'Unknown')} - {timestamp}")

    def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        """Send SMS via configured provider"""
        try:
            if self.config['sms_provider'] == 'twilio':
                return self._send_twilio_sms(phone, message)
            elif self.config['sms_provider'] == 'wachap':
                return self._send_wachap_message(phone, message)
            else:
                return False, "Unknown SMS provider"
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False, str(e)

    def _send_twilio_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            client = Client(self.config['twilio_account_sid'], self.config['twilio_auth_token'])
            sms = client.messages.create(
                body=message,
                from_=self.config['twilio_phone_number'],
                to=phone
            )
            return True, f"Sent (SID: {sms.sid})"
        except Exception as e:
            return False, str(e)

    def _send_wachap_message(self, phone: str, message: str) -> Tuple[bool, str]:
        """Send message via WaChap"""
        try:
            import requests
            url = f"{self.config['wachap_base_url'].rstrip('/')}/send"
            number = ''.join(c for c in phone if c.isdigit())
            if number.startswith('221'):
                number = number
            elif len(number) == 9:
                number = f"221{number}"

            payload = {
                "number": number,
                "type": "text",
                "message": message,
                "instance_id": self.config['wachap_instance_id'],
                "access_token": self.config['wachap_access_token']
            }

            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                return True, "Sent via WaChap"
            else:
                return False, f"WaChap error: {response.status_code}"
        except Exception as e:
            return False, str(e)

    def send_alert(self, alert_type: str, recipients: List[str], air_data: Dict,
                  school_name: str = "École", child_name: str = "votre enfant") -> Dict:
        """Send alert to specified recipients"""
        results = []
        sent_count = 0

        for recipient in recipients:
            phone = self._normalize_phone(recipient.get('phone', ''))
            if not phone:
                results.append({
                    'recipient': recipient.get('name', 'Unknown'),
                    'status': 'Invalid phone',
                    'reason': 'Invalid phone number'
                })
                continue

            can_send, reason = self.can_send_alert(alert_type, phone)
            if not can_send:
                results.append({
                    'recipient': recipient.get('name', 'Unknown'),
                    'status': 'Skipped',
                    'reason': reason
                })
                continue

            message = self.generate_alert_message(alert_type, air_data, school_name,
                                                recipient.get('child', child_name))
            success, send_reason = self.send_sms(phone, message)

            if success:
                today = datetime.now().strftime('%Y-%m-%d')
                key = f"{phone}_{alert_type}_{today}"
                self.sent_alerts[key] = {
                    'timestamp': datetime.now().isoformat(),
                    'recipient': recipient.get('name', 'Unknown'),
                    'child': recipient.get('child', child_name),
                    'message': message[:100] + '...' if len(message) > 100 else message
                }
                sent_count += 1

            results.append({
                'recipient': recipient.get('name', 'Unknown'),
                'status': 'Sent' if success else 'Failed',
                'reason': send_reason
            })

        if sent_count > 0:
            self.save_sent_alerts()

        return {
            'total_sent': sent_count,
            'total_attempted': len(recipients),
            'results': results
        }

def send_alert(alert_type: str, recipients: List[Dict], air_data: Dict) -> Dict:
    """Convenience function to send alerts"""
    service = AlertService()
    return service.send_alert(alert_type, recipients, air_data)
