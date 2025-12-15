"""
Database Module - SQLite operations for scan history and persistence
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for storing scan history"""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file (default: ~/.local/share/alienskull/scans.db)
        """
        if db_path is None:
            # Default to user's data directory
            data_dir = Path.home() / '.local' / 'share' / 'alienskull'
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / 'scans.db')

        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()

    def _get_connection(self):
        """Get thread-safe database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def _init_database(self):
        """Initialize database schema"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                # Scans table - individual scan sessions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        wifi_count INTEGER DEFAULT 0,
                        ble_count INTEGER DEFAULT 0,
                        high_risk_count INTEGER DEFAULT 0,
                        threat_level TEXT,
                        statistics TEXT,
                        anomalies TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Networks table - Wi-Fi networks detected
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS networks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_id INTEGER,
                        ssid TEXT,
                        bssid TEXT NOT NULL,
                        rssi INTEGER,
                        frequency INTEGER,
                        channel INTEGER,
                        security TEXT,
                        hidden INTEGER DEFAULT 0,
                        risk_score INTEGER,
                        risk_level TEXT,
                        risk_factors TEXT,
                        distance REAL,
                        angle REAL,
                        timestamp TEXT,
                        FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                    )
                ''')

                # Devices table - BLE devices detected
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_id INTEGER,
                        name TEXT,
                        mac TEXT NOT NULL,
                        rssi INTEGER,
                        device_type TEXT,
                        is_tracker INTEGER DEFAULT 0,
                        risk_score INTEGER,
                        risk_level TEXT,
                        risk_factors TEXT,
                        distance REAL,
                        angle REAL,
                        timestamp TEXT,
                        FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                    )
                ''')

                # Alerts table - notable events
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_id INTEGER,
                        type TEXT NOT NULL,
                        severity TEXT,
                        description TEXT,
                        metadata TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        acknowledged INTEGER DEFAULT 0,
                        FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                    )
                ''')

                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_networks_bssid ON networks(bssid)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_networks_scan_id ON networks(scan_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_scan_id ON devices(scan_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')

                conn.commit()
                conn.close()

                logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def save_scan(self, scan_results: Dict) -> Optional[int]:
        """
        Save complete scan results to database

        Args:
            scan_results: Analyzed scan results from RiskAnalyzer

        Returns:
            Scan ID or None if failed
        """
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                # Extract statistics
                stats = scan_results.get('statistics', {})
                wifi_count = len(scan_results.get('wifi', []))
                ble_count = len(scan_results.get('ble', []))

                # Count high risk items
                high_risk_count = 0
                for network in scan_results.get('wifi', []):
                    if network.get('risk_level') in ['high', 'critical']:
                        high_risk_count += 1
                for device in scan_results.get('ble', []):
                    if device.get('risk_level') in ['high', 'critical']:
                        high_risk_count += 1

                # Insert scan record
                cursor.execute('''
                    INSERT INTO scans (timestamp, wifi_count, ble_count, high_risk_count,
                                     threat_level, statistics, anomalies)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan_results.get('timestamp', datetime.now().isoformat()),
                    wifi_count,
                    ble_count,
                    high_risk_count,
                    stats.get('overall_threat_level', 'low'),
                    json.dumps(stats),
                    json.dumps(scan_results.get('anomalies', []))
                ))

                scan_id = cursor.lastrowid

                # Insert Wi-Fi networks
                for network in scan_results.get('wifi', []):
                    from .utils import calculate_radar_position

                    pos = calculate_radar_position(
                        network.get('rssi', -100),
                        network.get('bssid', 'unknown'),
                        network.get('frequency', 2437)
                    )

                    cursor.execute('''
                        INSERT INTO networks (scan_id, ssid, bssid, rssi, frequency, channel,
                                            security, hidden, risk_score, risk_level, risk_factors,
                                            distance, angle, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        scan_id,
                        network.get('ssid', '<hidden>'),
                        network.get('bssid', 'unknown'),
                        network.get('rssi', -100),
                        network.get('frequency', 0),
                        network.get('channel', 0),
                        network.get('security', 'Unknown'),
                        1 if network.get('hidden', False) else 0,
                        network.get('risk_score', 0),
                        network.get('risk_level', 'low'),
                        json.dumps(network.get('risk_factors', [])),
                        pos['distance'],
                        pos['angle'],
                        network.get('timestamp', datetime.now().isoformat())
                    ))

                # Insert BLE devices
                for device in scan_results.get('ble', []):
                    from .utils import calculate_radar_position

                    # BLE typically uses 2.4 GHz band
                    pos = calculate_radar_position(
                        device.get('rssi', -100),
                        device.get('mac', 'unknown'),
                        2437
                    )

                    cursor.execute('''
                        INSERT INTO devices (scan_id, name, mac, rssi, device_type, is_tracker,
                                           risk_score, risk_level, risk_factors,
                                           distance, angle, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        scan_id,
                        device.get('name', '<unnamed>'),
                        device.get('mac', 'unknown'),
                        device.get('rssi', -100),
                        device.get('device_type', 'Unknown'),
                        1 if device.get('is_tracker', False) else 0,
                        device.get('risk_score', 0),
                        device.get('risk_level', 'low'),
                        json.dumps(device.get('risk_factors', [])),
                        pos['distance'],
                        pos['angle'],
                        device.get('timestamp', datetime.now().isoformat())
                    ))

                # Insert anomaly alerts
                for anomaly in scan_results.get('anomalies', []):
                    cursor.execute('''
                        INSERT INTO alerts (scan_id, type, severity, description, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        scan_id,
                        anomaly.get('type', 'unknown'),
                        anomaly.get('severity', 'low'),
                        anomaly.get('description', ''),
                        json.dumps(anomaly)
                    ))

                conn.commit()
                conn.close()

                logger.info(f"Saved scan {scan_id} with {wifi_count} networks and {ble_count} devices")
                return scan_id

        except Exception as e:
            logger.error(f"Failed to save scan: {e}")
            return None

    def get_recent_scans(self, limit: int = 50) -> List[Dict]:
        """Get recent scan summaries"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, timestamp, wifi_count, ble_count, high_risk_count,
                           threat_level, created_at
                    FROM scans
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

                scans = []
                for row in cursor.fetchall():
                    scans.append(dict(row))

                conn.close()
                return scans

        except Exception as e:
            logger.error(f"Failed to get recent scans: {e}")
            return []

    def get_scan_details(self, scan_id: int) -> Optional[Dict]:
        """Get complete details for a specific scan"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                # Get scan info
                cursor.execute('SELECT * FROM scans WHERE id = ?', (scan_id,))
                scan_row = cursor.fetchone()

                if not scan_row:
                    conn.close()
                    return None

                scan = dict(scan_row)
                scan['statistics'] = json.loads(scan['statistics']) if scan['statistics'] else {}
                scan['anomalies'] = json.loads(scan['anomalies']) if scan['anomalies'] else []

                # Get networks
                cursor.execute('SELECT * FROM networks WHERE scan_id = ?', (scan_id,))
                networks = []
                for row in cursor.fetchall():
                    network = dict(row)
                    network['risk_factors'] = json.loads(network['risk_factors']) if network['risk_factors'] else []
                    networks.append(network)

                scan['wifi'] = networks

                # Get devices
                cursor.execute('SELECT * FROM devices WHERE scan_id = ?', (scan_id,))
                devices = []
                for row in cursor.fetchall():
                    device = dict(row)
                    device['risk_factors'] = json.loads(device['risk_factors']) if device['risk_factors'] else []
                    devices.append(device)

                scan['ble'] = devices

                # Get alerts
                cursor.execute('SELECT * FROM alerts WHERE scan_id = ?', (scan_id,))
                alerts = []
                for row in cursor.fetchall():
                    alert = dict(row)
                    alert['metadata'] = json.loads(alert['metadata']) if alert['metadata'] else {}
                    alerts.append(alert)

                scan['alerts'] = alerts

                conn.close()
                return scan

        except Exception as e:
            logger.error(f"Failed to get scan details: {e}")
            return None

    def cleanup_old_scans(self, days: int = 30) -> int:
        """Delete scans older than specified days"""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('DELETE FROM scans WHERE timestamp < ?', (cutoff,))
                deleted = cursor.rowcount

                conn.commit()
                conn.close()

                logger.info(f"Deleted {deleted} scans older than {days} days")
                return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup old scans: {e}")
            return 0

    def export_scans(self, format: str = 'json', days: int = 7) -> Optional[str]:
        """
        Export recent scans

        Args:
            format: 'json' or 'csv'
            days: Number of days to export

        Returns:
            Exported data as string or None
        """
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                if format == 'json':
                    # Export as JSON
                    cursor.execute('SELECT id FROM scans WHERE timestamp > ? ORDER BY timestamp DESC', (cutoff,))
                    scan_ids = [row[0] for row in cursor.fetchall()]

                    export_data = []
                    for scan_id in scan_ids:
                        scan = self.get_scan_details(scan_id)
                        if scan:
                            export_data.append(scan)

                    conn.close()
                    return json.dumps(export_data, indent=2)

                elif format == 'csv':
                    # Export as CSV
                    import csv
                    from io import StringIO

                    output = StringIO()
                    writer = csv.writer(output)

                    # Write headers
                    writer.writerow(['Timestamp', 'Type', 'ID', 'SSID/Name', 'RSSI', 'Security/Type',
                                   'Risk Score', 'Risk Level', 'Distance (m)'])

                    # Get networks
                    cursor.execute('''
                        SELECT s.timestamp, n.ssid, n.bssid, n.rssi, n.security,
                               n.risk_score, n.risk_level, n.distance
                        FROM networks n
                        JOIN scans s ON n.scan_id = s.id
                        WHERE s.timestamp > ?
                        ORDER BY s.timestamp DESC
                    ''', (cutoff,))

                    for row in cursor.fetchall():
                        writer.writerow(['WiFi'] + list(row))

                    # Get devices
                    cursor.execute('''
                        SELECT s.timestamp, d.name, d.mac, d.rssi, d.device_type,
                               d.risk_score, d.risk_level, d.distance
                        FROM devices d
                        JOIN scans s ON d.scan_id = s.id
                        WHERE s.timestamp > ?
                        ORDER BY s.timestamp DESC
                    ''', (cutoff,))

                    for row in cursor.fetchall():
                        writer.writerow(['BLE'] + list(row))

                    conn.close()
                    return output.getvalue()

                else:
                    logger.error(f"Unknown export format: {format}")
                    return None

        except Exception as e:
            logger.error(f"Failed to export scans: {e}")
            return None
