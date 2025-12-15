"""
Scanner Module - Wi-Fi and BLE scanning using Termux API
Handles all device detection and signal measurement
"""

import json
import subprocess
import logging
from typing import List, Dict, Optional
from datetime import datetime
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WifiScanner:
    """Wi-Fi network scanner using Termux API"""

    def __init__(self):
        self.last_scan = None
        self.lock = threading.Lock()

    def scan(self) -> List[Dict]:
        """
        Execute Wi-Fi scan using termux-wifi-scaninfo

        Returns:
            List of network dictionaries with SSID, BSSID, RSSI, security, etc.
        """
        try:
            # Execute Termux API command
            result = subprocess.run(
                ['termux-wifi-scaninfo'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error(f"Wi-Fi scan failed: {result.stderr}")
                return []

            # Parse JSON output
            data = json.loads(result.stdout)
            networks = []

            for network in data:
                try:
                    # Extract and normalize network info
                    network_info = {
                        'type': 'wifi',
                        'ssid': network.get('ssid', '<hidden>'),
                        'bssid': network.get('bssid', 'unknown'),
                        'rssi': network.get('level', -100),
                        'frequency': network.get('frequency', 0),
                        'channel': self._freq_to_channel(network.get('frequency', 0)),
                        'capabilities': network.get('capabilities', ''),
                        'timestamp': datetime.now().isoformat(),
                        'hidden': not network.get('ssid') or network.get('ssid') == ''
                    }

                    # Extract security type
                    network_info['security'] = self._parse_security(network_info['capabilities'])

                    networks.append(network_info)

                except Exception as e:
                    logger.warning(f"Error parsing network: {e}")
                    continue

            with self.lock:
                self.last_scan = datetime.now()

            logger.info(f"Scanned {len(networks)} Wi-Fi networks")
            return networks

        except subprocess.TimeoutExpired:
            logger.error("Wi-Fi scan timeout")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scan results: {e}")
            return []
        except FileNotFoundError:
            logger.error("Termux API not found. Install Termux:API from F-Droid")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during Wi-Fi scan: {e}")
            return []

    def _parse_security(self, capabilities: str) -> str:
        """Extract security type from capabilities string"""
        caps_upper = capabilities.upper()

        if 'WPA3' in caps_upper:
            return 'WPA3'
        elif 'WPA2' in caps_upper:
            return 'WPA2'
        elif 'WPA' in caps_upper:
            return 'WPA'
        elif 'WEP' in caps_upper:
            return 'WEP'
        elif 'ESS' in caps_upper or caps_upper:
            return 'Open'
        else:
            return 'Unknown'

    def _freq_to_channel(self, frequency: int) -> int:
        """Convert frequency (MHz) to Wi-Fi channel number"""
        if frequency == 0:
            return 0
        elif 2412 <= frequency <= 2484:
            # 2.4 GHz band
            return (frequency - 2407) // 5
        elif 5170 <= frequency <= 5825:
            # 5 GHz band
            return (frequency - 5000) // 5
        else:
            return 0


class BLEScanner:
    """Bluetooth Low Energy scanner using Termux API"""

    def __init__(self):
        self.last_scan = None
        self.lock = threading.Lock()
        # Known tracker MAC prefixes
        self.tracker_prefixes = {
            'AC:23:3F': 'Apple AirTag',
            '38:FE:5E': 'Tile Tracker',
            'E4:04:39': 'Samsung SmartTag',
            '00:A0:50': 'Generic BLE Tracker'
        }

    def scan(self, duration: int = 5) -> List[Dict]:
        """
        Execute BLE scan using termux-bluetooth-scaninfo

        Args:
            duration: Scan duration in seconds

        Returns:
            List of device dictionaries with name, MAC, RSSI, type, etc.
        """
        try:
            # Execute Termux API command
            result = subprocess.run(
                ['termux-bluetooth-scaninfo'],
                capture_output=True,
                text=True,
                timeout=duration + 5
            )

            if result.returncode != 0:
                logger.error(f"BLE scan failed: {result.stderr}")
                return []

            # Parse JSON output
            data = json.loads(result.stdout)
            devices = []

            for device in data:
                try:
                    mac = device.get('address', 'unknown')

                    device_info = {
                        'type': 'ble',
                        'name': device.get('name', '<unnamed>'),
                        'mac': mac,
                        'rssi': device.get('rssi', -100),
                        'timestamp': datetime.now().isoformat(),
                        'device_type': self._identify_device_type(mac, device.get('name', '')),
                        'is_tracker': self._is_tracker(mac)
                    }

                    devices.append(device_info)

                except Exception as e:
                    logger.warning(f"Error parsing BLE device: {e}")
                    continue

            with self.lock:
                self.last_scan = datetime.now()

            logger.info(f"Scanned {len(devices)} BLE devices")
            return devices

        except subprocess.TimeoutExpired:
            logger.error("BLE scan timeout")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BLE results: {e}")
            return []
        except FileNotFoundError:
            logger.error("Termux API not found. Install Termux:API from F-Droid")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during BLE scan: {e}")
            return []

    def _is_tracker(self, mac: str) -> bool:
        """Check if device is a known tracker based on MAC prefix"""
        mac_prefix = mac[:8].upper()
        return mac_prefix in self.tracker_prefixes

    def _identify_device_type(self, mac: str, name: str) -> str:
        """Identify device type based on MAC and name"""
        mac_prefix = mac[:8].upper()

        # Check known trackers
        if mac_prefix in self.tracker_prefixes:
            return self.tracker_prefixes[mac_prefix]

        # Identify by name patterns
        name_lower = name.lower()
        if 'watch' in name_lower or 'band' in name_lower:
            return 'Wearable'
        elif 'phone' in name_lower or 'android' in name_lower or 'iphone' in name_lower:
            return 'Phone'
        elif 'beacon' in name_lower:
            return 'Beacon'
        elif 'headset' in name_lower or 'earbuds' in name_lower or 'headphones' in name_lower:
            return 'Audio Device'
        else:
            return 'Unknown BLE Device'


class ScanCoordinator:
    """Coordinates Wi-Fi and BLE scanning with thread safety"""

    def __init__(self, scan_interval: int = 5, enable_ble: bool = True):
        self.wifi_scanner = WifiScanner()
        self.ble_scanner = BLEScanner() if enable_ble else None
        self.scan_interval = scan_interval
        self.enable_ble = enable_ble
        self.running = False
        self.scan_thread = None
        self.callbacks = []

    def register_callback(self, callback):
        """Register callback function to receive scan results"""
        self.callbacks.append(callback)

    def start(self):
        """Start continuous scanning in background thread"""
        if self.running:
            logger.warning("Scanner already running")
            return

        self.running = True
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        logger.info("Scan coordinator started")

    def stop(self):
        """Stop background scanning"""
        self.running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=5)
        logger.info("Scan coordinator stopped")

    def _scan_loop(self):
        """Main scanning loop running in background thread"""
        import time

        while self.running:
            try:
                # Perform scans
                results = {
                    'wifi': self.wifi_scanner.scan(),
                    'ble': self.ble_scanner.scan() if self.enable_ble else [],
                    'timestamp': datetime.now().isoformat()
                }

                # Notify all callbacks
                for callback in self.callbacks:
                    try:
                        callback(results)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                # Wait for next scan
                time.sleep(self.scan_interval)

            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                time.sleep(self.scan_interval)

    def scan_once(self) -> Dict:
        """Perform single scan and return results immediately"""
        results = {
            'wifi': self.wifi_scanner.scan(),
            'ble': self.ble_scanner.scan() if self.enable_ble else [],
            'timestamp': datetime.now().isoformat()
        }
        return results
