#!/usr/bin/env python3
"""
AlienSkull Server - Main application entry point
Flask + SocketIO server for real-time surveillance detection
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Add core modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.scanner import ScanCoordinator
from core.analyzer import RiskAnalyzer
from core.database import Database
from core.utils import calculate_radar_position, get_risk_color

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'alienskull-tactical-surveillance-killer'
app.config['JSON_SORT_KEYS'] = False

# Enable CORS for development
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Load configuration
CONFIG_DIR = Path.home() / '.config' / 'alienskull'
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / 'config.json'

DEFAULT_CONFIG = {
    "scan_interval": 5,
    "max_display_distance": 100,
    "history_retention_days": 30,
    "risk_thresholds": {
        "low": 30,
        "medium": 60,
        "high": 80
    },
    "alerts": {
        "enabled": True,
        "new_network": True,
        "high_risk": True
    },
    "ble_scanning": True,
    "port": 5000,
    "host": "127.0.0.1"
}

def load_config():
    """Load configuration from file or create default"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        logger.info("Created default configuration")
        return DEFAULT_CONFIG

config = load_config()

# Initialize core components
scanner = ScanCoordinator(
    scan_interval=config['scan_interval'],
    enable_ble=config['ble_scanning']
)
analyzer = RiskAnalyzer()
database = Database()

# Global state
scanning_active = False


def process_scan_results(results):
    """Process scan results and broadcast to clients"""
    try:
        # Analyze results
        analyzed = analyzer.analyze_scan_results(results)

        # Add radar positions
        for network in analyzed['wifi']:
            pos = calculate_radar_position(
                network['rssi'],
                network['bssid'],
                network.get('frequency', 2437),
                config['max_display_distance']
            )
            network['position'] = pos
            network['color'] = get_risk_color(network['risk_level'])

        for device in analyzed['ble']:
            pos = calculate_radar_position(
                device['rssi'],
                device['mac'],
                2437,  # BLE uses 2.4 GHz
                config['max_display_distance']
            )
            device['position'] = pos
            device['color'] = get_risk_color(device['risk_level'])

        # Save to database
        scan_id = database.save_scan(analyzed)
        analyzed['scan_id'] = scan_id

        # Broadcast to all connected clients
        socketio.emit('scan_update', analyzed, namespace='/')

        logger.info(f"Processed scan: {len(analyzed['wifi'])} Wi-Fi, {len(analyzed['ble'])} BLE")

    except Exception as e:
        logger.error(f"Error processing scan results: {e}")


# Register scanner callback
scanner.register_callback(process_scan_results)


# Flask routes

@app.route('/')
def index():
    """Main radar view"""
    return render_template('index.html', config=config)


@app.route('/timeline')
def timeline():
    """Timeline/history view"""
    return render_template('timeline.html', config=config)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    global config
    try:
        new_config = request.get_json()
        config.update(new_config)

        # Save to file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        # Update scanner settings
        scanner.scan_interval = config['scan_interval']
        scanner.enable_ble = config['ble_scanning']

        return jsonify({"status": "success", "config": config})

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/scan/start', methods=['POST'])
def start_scanning():
    """Start continuous scanning"""
    global scanning_active
    try:
        if not scanning_active:
            scanner.start()
            scanning_active = True
            logger.info("Scanning started")
            return jsonify({"status": "success", "message": "Scanning started"})
        else:
            return jsonify({"status": "info", "message": "Scanning already active"})

    except Exception as e:
        logger.error(f"Failed to start scanning: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/scan/stop', methods=['POST'])
def stop_scanning():
    """Stop continuous scanning"""
    global scanning_active
    try:
        if scanning_active:
            scanner.stop()
            scanning_active = False
            logger.info("Scanning stopped")
            return jsonify({"status": "success", "message": "Scanning stopped"})
        else:
            return jsonify({"status": "info", "message": "Scanning not active"})

    except Exception as e:
        logger.error(f"Failed to stop scanning: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/scan/once', methods=['POST'])
def scan_once():
    """Perform single scan"""
    try:
        results = scanner.scan_once()
        analyzed = analyzer.analyze_scan_results(results)

        # Add positions
        for network in analyzed['wifi']:
            pos = calculate_radar_position(
                network['rssi'],
                network['bssid'],
                network.get('frequency', 2437),
                config['max_display_distance']
            )
            network['position'] = pos
            network['color'] = get_risk_color(network['risk_level'])

        for device in analyzed['ble']:
            pos = calculate_radar_position(
                device['rssi'],
                device['mac'],
                2437,
                config['max_display_distance']
            )
            device['position'] = pos
            device['color'] = get_risk_color(device['risk_level'])

        # Save to database
        scan_id = database.save_scan(analyzed)
        analyzed['scan_id'] = scan_id

        return jsonify({"status": "success", "data": analyzed})

    except Exception as e:
        logger.error(f"Failed to perform scan: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        "scanning": scanning_active,
        "config": config,
        "version": "1.0.0"
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get scan history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        scans = database.get_recent_scans(limit)
        return jsonify({"status": "success", "scans": scans})

    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/history/<int:scan_id>', methods=['GET'])
def get_scan_detail(scan_id):
    """Get detailed scan information"""
    try:
        scan = database.get_scan_details(scan_id)
        if scan:
            return jsonify({"status": "success", "scan": scan})
        else:
            return jsonify({"status": "error", "message": "Scan not found"}), 404

    except Exception as e:
        logger.error(f"Failed to get scan details: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/export', methods=['GET'])
def export_data():
    """Export scan data"""
    try:
        format_type = request.args.get('format', 'json')
        days = request.args.get('days', 7, type=int)

        data = database.export_scans(format_type, days)

        if data:
            if format_type == 'json':
                return jsonify({"status": "success", "data": json.loads(data)})
            elif format_type == 'csv':
                from flask import Response
                return Response(
                    data,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=alienskull_export.csv'}
                )
        else:
            return jsonify({"status": "error", "message": "Export failed"}), 500

    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old scan data"""
    try:
        days = request.get_json().get('days', 30)
        deleted = database.cleanup_old_scans(days)
        analyzer.clear_history(days)

        return jsonify({
            "status": "success",
            "message": f"Deleted {deleted} old scans"
        })

    except Exception as e:
        logger.error(f"Failed to cleanup database: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# SocketIO event handlers

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'scanning': scanning_active})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('request_scan')
def handle_scan_request():
    """Handle client scan request"""
    try:
        results = scanner.scan_once()
        process_scan_results(results)
    except Exception as e:
        logger.error(f"Scan request failed: {e}")
        emit('error', {'message': str(e)})


# Error handlers

@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# Startup banner

def print_banner():
    """Print startup banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     █████╗ ██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗║
    ║    ██╔══██╗██║     ██║██╔════╝████╗  ██║██╔════╝██║ ██╔╝║
    ║    ███████║██║     ██║█████╗  ██╔██╗ ██║███████╗█████╔╝ ║
    ║    ██╔══██║██║     ██║██╔══╝  ██║╚██╗██║╚════██║██╔═██╗ ║
    ║    ██║  ██║███████╗██║███████╗██║ ╚████║███████║██║  ██╗║
    ║    ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝║
    ║                                                           ║
    ║              SURVEILLANCE KILLER v1.0.0                   ║
    ║          Privacy-First Threat Detection System            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

    [*] Server starting on http://{host}:{port}
    [*] Scan interval: {interval}s
    [*] BLE scanning: {ble}
    [*] Database: {db}
    [*] Config: {config}

    [!] Educational/Research Use Only
    [!] Passive scanning - no active attacks
    [!] Respect local regulations

    """
    print(banner.format(
        host=config['host'],
        port=config['port'],
        interval=config['scan_interval'],
        ble='Enabled' if config['ble_scanning'] else 'Disabled',
        db=database.db_path,
        config=CONFIG_FILE
    ))


def main():
    """Main entry point"""
    print_banner()

    # Start server
    try:
        socketio.run(
            app,
            host=config['host'],
            port=config['port'],
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        scanner.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
