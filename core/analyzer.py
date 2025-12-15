"""
Analyzer Module - Risk scoring and threat detection
Evaluates networks and devices for potential surveillance threats
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Analyzes networks and devices to calculate risk scores"""

    def __init__(self):
        # Risk thresholds
        self.RISK_LOW = 30
        self.RISK_MEDIUM = 60
        self.RISK_HIGH = 80

        # Tracking for anomaly detection
        self.network_history = defaultdict(list)
        self.device_history = defaultdict(list)
        self.known_networks = set()
        self.known_devices = set()

    def analyze_wifi(self, network: Dict) -> Dict:
        """
        Analyze a Wi-Fi network and calculate risk score

        Args:
            network: Network dictionary from scanner

        Returns:
            Network dict with added 'risk_score', 'risk_level', 'risk_factors'
        """
        score = 0
        factors = []

        # Security type scoring (0-50 points)
        security = network.get('security', 'Unknown')

        if security == 'WEP':
            score += 50
            factors.append('Critical: WEP encryption (easily cracked)')
        elif security == 'Open':
            score += 40
            factors.append('High: Open network (no encryption)')
        elif security == 'WPA':
            score += 20
            factors.append('Medium: Old WPA encryption')
        elif security == 'WPA2':
            score += 10
            factors.append('Low: WPA2 encryption (standard)')
        elif security == 'WPA3':
            score += 0
            factors.append('Secure: WPA3 encryption')
        else:
            score += 15
            factors.append('Unknown security type')

        # Signal strength scoring (0-30 points)
        rssi = network.get('rssi', -100)

        if rssi > -40:
            score += 30
            factors.append('Very strong signal (< 5m away, very suspicious)')
        elif rssi > -60:
            score += 15
            factors.append('Strong signal (5-20m away)')
        elif rssi > -80:
            score += 5
            factors.append('Moderate signal (20-50m away)')

        # Hidden SSID (20 points)
        if network.get('hidden', False):
            score += 20
            factors.append('Hidden SSID (cloaked network)')

        # Unusual characteristics (10 points each)
        ssid = network.get('ssid', '')

        # Generic/suspicious SSID patterns
        suspicious_patterns = ['test', 'default', 'admin', 'hidden', 'nomap']
        if any(pattern in ssid.lower() for pattern in suspicious_patterns):
            score += 10
            factors.append(f'Suspicious SSID pattern detected')

        # Anomaly detection - new network
        bssid = network.get('bssid', 'unknown')
        if bssid not in self.known_networks:
            score += 5
            factors.append('New network detected')
            self.known_networks.add(bssid)

        # Cap score at 100
        score = min(score, 100)

        # Determine risk level
        if score >= self.RISK_HIGH:
            risk_level = 'high'
        elif score >= self.RISK_MEDIUM:
            risk_level = 'medium'
        elif score >= self.RISK_LOW:
            risk_level = 'low'
        else:
            risk_level = 'minimal'

        # Add analysis results to network
        network['risk_score'] = score
        network['risk_level'] = risk_level
        network['risk_factors'] = factors

        # Track in history
        self.network_history[bssid].append({
            'timestamp': datetime.now(),
            'rssi': rssi,
            'score': score
        })

        return network

    def analyze_ble(self, device: Dict) -> Dict:
        """
        Analyze a BLE device and calculate risk score

        Args:
            device: Device dictionary from scanner

        Returns:
            Device dict with added 'risk_score', 'risk_level', 'risk_factors'
        """
        score = 0
        factors = []

        # Tracker detection (50 points)
        if device.get('is_tracker', False):
            score += 50
            device_type = device.get('device_type', 'Unknown')
            factors.append(f'Known tracker detected: {device_type}')

        # Signal strength scoring (0-30 points)
        rssi = device.get('rssi', -100)

        if rssi > -40:
            score += 30
            factors.append('Very strong signal (< 2m away)')
        elif rssi > -60:
            score += 15
            factors.append('Strong signal (2-10m away)')
        elif rssi > -80:
            score += 5
            factors.append('Moderate signal (10-30m away)')

        # Unnamed devices (suspicious) (15 points)
        if device.get('name', '<unnamed>') == '<unnamed>':
            score += 15
            factors.append('Unnamed device (hidden identity)')

        # Anomaly detection - new device
        mac = device.get('mac', 'unknown')
        if mac not in self.known_devices:
            score += 5
            factors.append('New BLE device detected')
            self.known_devices.add(mac)

        # Cap score at 100
        score = min(score, 100)

        # Determine risk level
        if score >= self.RISK_HIGH:
            risk_level = 'high'
        elif score >= self.RISK_MEDIUM:
            risk_level = 'medium'
        elif score >= self.RISK_LOW:
            risk_level = 'low'
        else:
            risk_level = 'minimal'

        # Add analysis results to device
        device['risk_score'] = score
        device['risk_level'] = risk_level
        device['risk_factors'] = factors

        # Track in history
        self.device_history[mac].append({
            'timestamp': datetime.now(),
            'rssi': rssi,
            'score': score
        })

        return device

    def analyze_scan_results(self, results: Dict) -> Dict:
        """
        Analyze complete scan results (Wi-Fi + BLE)

        Args:
            results: Scan results dictionary with 'wifi' and 'ble' lists

        Returns:
            Enhanced results with risk analysis and statistics
        """
        # Analyze each network
        wifi_analyzed = [self.analyze_wifi(network.copy()) for network in results.get('wifi', [])]

        # Analyze each BLE device
        ble_analyzed = [self.analyze_ble(device.copy()) for device in results.get('ble', [])]

        # Calculate statistics
        stats = self._calculate_statistics(wifi_analyzed, ble_analyzed)

        # Detect anomalies
        anomalies = self._detect_anomalies(wifi_analyzed, ble_analyzed)

        return {
            'wifi': wifi_analyzed,
            'ble': ble_analyzed,
            'statistics': stats,
            'anomalies': anomalies,
            'timestamp': results.get('timestamp', datetime.now().isoformat())
        }

    def _calculate_statistics(self, wifi_networks: List[Dict], ble_devices: List[Dict]) -> Dict:
        """Calculate summary statistics for scan results"""

        # Wi-Fi stats
        wifi_total = len(wifi_networks)
        wifi_by_risk = {
            'high': len([n for n in wifi_networks if n['risk_level'] == 'high']),
            'medium': len([n for n in wifi_networks if n['risk_level'] == 'medium']),
            'low': len([n for n in wifi_networks if n['risk_level'] == 'low']),
            'minimal': len([n for n in wifi_networks if n['risk_level'] == 'minimal'])
        }
        wifi_by_security = {}
        for network in wifi_networks:
            security = network.get('security', 'Unknown')
            wifi_by_security[security] = wifi_by_security.get(security, 0) + 1

        # BLE stats
        ble_total = len(ble_devices)
        ble_by_risk = {
            'high': len([d for d in ble_devices if d['risk_level'] == 'high']),
            'medium': len([d for d in ble_devices if d['risk_level'] == 'medium']),
            'low': len([d for d in ble_devices if d['risk_level'] == 'low']),
            'minimal': len([d for d in ble_devices if d['risk_level'] == 'minimal'])
        }
        trackers_detected = len([d for d in ble_devices if d.get('is_tracker', False)])

        return {
            'wifi': {
                'total': wifi_total,
                'by_risk': wifi_by_risk,
                'by_security': wifi_by_security
            },
            'ble': {
                'total': ble_total,
                'by_risk': ble_by_risk,
                'trackers': trackers_detected
            },
            'overall_threat_level': self._calculate_threat_level(wifi_by_risk, ble_by_risk)
        }

    def _calculate_threat_level(self, wifi_risk: Dict, ble_risk: Dict) -> str:
        """Calculate overall threat level for environment"""
        total_high = wifi_risk['high'] + ble_risk['high']
        total_medium = wifi_risk['medium'] + ble_risk['medium']

        if total_high >= 3:
            return 'critical'
        elif total_high >= 1 or total_medium >= 5:
            return 'elevated'
        elif total_medium >= 1:
            return 'moderate'
        else:
            return 'low'

    def _detect_anomalies(self, wifi_networks: List[Dict], ble_devices: List[Dict]) -> List[Dict]:
        """Detect anomalous patterns in scan results"""
        anomalies = []

        # Check for multiple hidden networks
        hidden_networks = [n for n in wifi_networks if n.get('hidden', False)]
        if len(hidden_networks) >= 3:
            anomalies.append({
                'type': 'multiple_hidden_networks',
                'severity': 'medium',
                'description': f'{len(hidden_networks)} hidden networks detected',
                'count': len(hidden_networks)
            })

        # Check for multiple trackers
        trackers = [d for d in ble_devices if d.get('is_tracker', False)]
        if len(trackers) >= 2:
            anomalies.append({
                'type': 'multiple_trackers',
                'severity': 'high',
                'description': f'{len(trackers)} tracking devices detected',
                'devices': [t.get('device_type', 'Unknown') for t in trackers]
            })

        # Check for WEP networks (critical vulnerability)
        wep_networks = [n for n in wifi_networks if n.get('security') == 'WEP']
        if wep_networks:
            anomalies.append({
                'type': 'wep_encryption_detected',
                'severity': 'critical',
                'description': f'{len(wep_networks)} network(s) using broken WEP encryption',
                'count': len(wep_networks)
            })

        # Check for very strong nearby signals (potential surveillance)
        very_close_wifi = [n for n in wifi_networks if n.get('rssi', -100) > -40]
        if len(very_close_wifi) >= 2:
            anomalies.append({
                'type': 'multiple_close_networks',
                'severity': 'medium',
                'description': f'{len(very_close_wifi)} networks with very strong signal detected',
                'count': len(very_close_wifi)
            })

        return anomalies

    def get_network_history(self, bssid: str, hours: int = 24) -> List[Dict]:
        """Get historical data for a specific network"""
        cutoff = datetime.now() - timedelta(hours=hours)
        history = self.network_history.get(bssid, [])
        return [h for h in history if h['timestamp'] > cutoff]

    def get_device_history(self, mac: str, hours: int = 24) -> List[Dict]:
        """Get historical data for a specific BLE device"""
        cutoff = datetime.now() - timedelta(hours=hours)
        history = self.device_history.get(mac, [])
        return [h for h in history if h['timestamp'] > cutoff]

    def clear_history(self, older_than_days: int = 30):
        """Clear old history data to prevent memory bloat"""
        cutoff = datetime.now() - timedelta(days=older_than_days)

        # Clean network history
        for bssid in list(self.network_history.keys()):
            self.network_history[bssid] = [
                h for h in self.network_history[bssid]
                if h['timestamp'] > cutoff
            ]
            if not self.network_history[bssid]:
                del self.network_history[bssid]

        # Clean device history
        for mac in list(self.device_history.keys()):
            self.device_history[mac] = [
                h for h in self.device_history[mac]
                if h['timestamp'] > cutoff
            ]
            if not self.device_history[mac]:
                del self.device_history[mac]

        logger.info(f"Cleared history older than {older_than_days} days")
