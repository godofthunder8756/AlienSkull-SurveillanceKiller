# AlienSkull: Surveillance Killer

## Project Overview

AlienSkull is an open-source Android reconnaissance tool that transforms your phone into a portable security audit device. Running entirely offline via Termux, it scans and visualizes nearby Wi-Fi networks and Bluetooth devices on a real-time tactical radar HUD, helping identify potential surveillance risks and network security issues.

**Philosophy**: No camera. No mic. Just signal. Complete privacy-first design with all processing local to the device.

## Core Features

- **Live Wi-Fi Scanning**: Real-time detection with RSSI-based distance estimation
- **BLE Device Detection**: Scan for Bluetooth Low Energy devices (trackers, beacons, etc.)
- **Tactical Radar HUD**: Satellite-style visualization with risk-based color coding
- **Risk Scoring Engine**: Automatic threat assessment based on security type, signal strength, and behavior patterns
- **Intel Timeline**: Comprehensive scan history with export capabilities
- **Offline-First**: Zero cloud dependencies, no data leaks
- **Clean UI**: Dark tactical interface optimized for field use

## Technology Stack

### Backend
- **Python 3.11+** with Flask/Flask-SocketIO
- **Termux API** for Android sensor access
- **SQLite** for scan history persistence
- Real-time WebSocket communication

### Frontend
- **HTML5 Canvas** for radar visualization
- **Vanilla JavaScript** (no frameworks - keep it lightweight)
- **CSS3** with dark tactical theme
- **WebSocket** for live updates

### Deployment
- **Termux** on Android (primary platform)
- **F-Droid** for Termux + Termux:API installation
- Bash installation scripts for easy setup

## Project Structure

```
alienskull/
├── README.md
├── CLAUDE.md
├── LICENSE (GPL-3.0)
├── install.sh
├── requirements.txt
├── server.py
├── core/
│   ├── __init__.py
│   ├── scanner.py          # Wi-Fi/BLE scanning logic
│   ├── analyzer.py         # Risk scoring and threat detection
│   ├── database.py         # SQLite operations
│   └── utils.py            # Distance calculation, MAC lookup
├── static/
│   ├── css/
│   │   └── style.css       # Tactical HUD styling
│   ├── js/
│   │   ├── radar.js        # Canvas radar visualization
│   │   ├── websocket.js    # Real-time communication
│   │   └── timeline.js     # History and export
│   └── assets/
│       └── logo.svg        # AlienSkull branding
├── templates/
│   ├── index.html          # Main radar view
│   └── timeline.html       # Scan history view
└── tests/
    ├── test_scanner.py
    ├── test_analyzer.py
    └── test_database.py
```

## Implementation Plan

### Phase 1: Core Infrastructure (Priority 1)

**1.1 Scanner Module (`core/scanner.py`)**
- Implement `WifiScanner` class using `termux-wifi-scaninfo`
- Implement `BLEScanner` class using `termux-bluetooth-scaninfo`
- Parse JSON output from Termux API
- Handle errors gracefully (permissions, API failures)
- RSSI to distance conversion using Free Space Path Loss formula
- Thread-safe operation for background scanning

**1.2 Database Layer (`core/database.py`)**
- SQLite schema for networks and scan sessions
- Tables: `scans`, `networks`, `devices`, `alerts`
- CRUD operations with proper indexing
- Automatic cleanup of old data (configurable retention)
- Export functions (JSON, CSV)

**1.3 Flask Server (`server.py`)**
- Main application entry point
- WebSocket setup with Flask-SocketIO
- REST API endpoints for history/configuration
- Background thread for continuous scanning
- Rate limiting to prevent resource exhaustion

### Phase 2: Analysis Engine (Priority 1)

**2.1 Risk Analyzer (`core/analyzer.py`)**
- Security scoring based on encryption type
  - Open networks: High risk
  - WEP: Critical risk
  - WPA/WPA2: Medium risk
  - WPA3: Low risk
- Signal strength analysis (unusually strong signals nearby)
- Hidden SSID detection
- MAC vendor lookup for device identification
- Anomaly detection (new devices, signal changes)
- Tracker identification (AirTags, Tiles, SmartTags)

**2.2 Utility Functions (`core/utils.py`)**
- RSSI to distance calculation
  ```python
  distance = 10 ** ((27.55 - (20 * log10(freq_mhz)) + abs(rssi)) / 20)
  ```
- MAC address vendor lookup (offline database)
- Coordinate calculation for radar positioning
- Hash-based positioning (deterministic placement on radar)

### Phase 3: Radar Visualization (Priority 1)

**3.1 Radar Canvas (`static/js/radar.js`)**
- Circular radar with range rings (25m, 50m, 75m, 100m)
- Network plotting based on distance and direction
- Color coding by risk level:
  - `#00f5ff` (cyan): Low risk
  - `#ffba08` (amber): Medium risk
  - `#ff0054` (red): High risk
  - `#9d4edd` (purple): BLE devices
- Sweep animation effect
- Click to view network details
- Real-time updates without full redraw

**3.2 WebSocket Integration (`static/js/websocket.js`)**
- Connect to Flask-SocketIO server
- Handle `scan_update` events
- Automatic reconnection on disconnect
- Update radar and timeline in real-time

**3.3 UI Styling (`static/css/style.css`)**
- Dark tactical theme (#000814 background)
- Glowing blue accents (#003566, #00f5ff)
- Monospace fonts for technical data
- Responsive layout for different screen sizes
- Accessibility considerations

### Phase 4: Timeline & History (Priority 2)

**4.1 Timeline View (`static/js/timeline.js`)**
- Chronological list of scan sessions
- Filter by time range, risk level
- Detailed network information cards
- Export functionality (JSON, CSV)
- Search/filter capabilities

**4.2 Templates (`templates/`)**
- Main radar view with side panel
- Timeline view with filters
- Shared navigation between views

### Phase 5: Installation & Setup (Priority 1)

**5.1 Installation Script (`install.sh`)**
```bash
#!/bin/bash
# Install system dependencies via Termux
# Create directory structure
# Install Python packages
# Initialize database
# Generate config file
# Create launcher script
```

**5.2 Documentation**
- README with installation instructions
- Security and legal disclaimers
- Configuration options
- Troubleshooting guide
- Screenshots and demos

## Technical Specifications

### Wi-Fi Scanning
- Use `termux-wifi-scaninfo` command
- Parse JSON output containing:
  - SSID, BSSID, frequency, level (RSSI)
  - Capabilities (security type)
  - Channel width
- Scan interval: 5 seconds (configurable)
- Distance calculation accuracy: ±20m

### BLE Scanning
- Use `termux-bluetooth-scaninfo` command
- Detect: beacons, trackers, wearables
- Identify known tracker MAC prefixes
- Passive scanning only (no connections)

### Risk Scoring Algorithm
```python
score = 0
# Security type (0-50 points)
if 'WEP' in security: score += 50
elif 'WPA3' in security: score += 0
elif 'WPA2' in security: score += 10
elif 'WPA' in security: score += 20
else: score += 40  # Open network

# Signal strength (0-30 points)
if rssi > -40: score += 30  # Very close, suspicious
elif rssi > -60: score += 15

# Behavior (0-20 points)
if hidden_ssid: score += 20
if unusual_mac_vendor: score += 10

return min(score, 100)
```

### Radar Positioning
- Networks placed based on:
  - **Distance**: RSSI-derived distance from center
  - **Angle**: Deterministic hash of BSSID for consistent placement
- Center = device location
- Range rings at 25m intervals (max 100m display)

## Configuration Options

Configuration stored in `~/.config/alienskull/config.json`:

```json
{
  "scan_interval": 5,
  "max_display_distance": 100,
  "history_retention_days": 30,
  "risk_thresholds": {
    "low": 30,
    "medium": 60,
    "high": 80
  },
  "alerts": {
    "enabled": true,
    "new_network": true,
    "high_risk": true
  },
  "ble_scanning": true,
  "port": 5000
}
```

## Security Considerations

### Privacy Protection
- All data stored locally on device
- No network transmission of scan data
- Option to anonymize MAC addresses in exports
- Clear data retention policies

### Legal Compliance
- Passive scanning only (no packet injection)
- Disclaimer about local regulations
- Educational/security research purposes
- User responsibility for legal use

### Code Security
- Input validation on all Termux API calls
- SQL injection prevention with parameterized queries
- XSS prevention in web UI
- CSP headers on Flask app

## Testing Strategy

### Unit Tests
- Scanner functions with mock Termux API output
- Risk scoring algorithm validation
- Distance calculation accuracy
- Database CRUD operations

### Integration Tests
- Full scan cycle from API to database
- WebSocket message flow
- Radar rendering with test data

### Manual Testing
- Test on multiple Android versions (8-14)
- Various device types (low-end to high-end)
- Different permission scenarios
- Network stress testing (many APs)

## Performance Requirements

- Scan cycle: < 2 seconds
- UI update latency: < 100ms
- Memory usage: < 100MB
- Battery impact: Minimal (background scan optimization)
- Database: Handle 10,000+ network entries

## Future Enhancements (Out of Scope for v1.0)

- GPS integration for wardriving mode
- 3D visualization option
- Packet capture integration
- Deauth detection
- Network mapping over time
- Collaborative scanning (multi-device)
- Machine learning for anomaly detection

## Development Guidelines

### Code Style
- PEP 8 for Python code
- ESLint recommended rules for JavaScript
- Clear docstrings for all functions
- Type hints in Python where beneficial

### Git Workflow
- Feature branches from `main`
- Descriptive commit messages
- Pull requests for major changes
- Semantic versioning (v1.0.0)

### Documentation
- Inline comments for complex logic
- README with examples
- API documentation for endpoints
- User guide with screenshots

## Success Criteria

v1.0 is complete when:
- ✅ Wi-Fi scanning works reliably on Android
- ✅ Radar visualization displays networks accurately
- ✅ Risk scoring produces meaningful results
- ✅ Timeline shows scan history
- ✅ Installation script works on fresh Termux install
- ✅ All core features documented
- ✅ Basic unit tests passing
- ✅ No critical security issues

## Notes for Claude Code

This is a **privacy-focused security tool** for identifying potential surveillance threats. The goal is to make security research accessible while maintaining the highest standards of privacy and legal compliance.

When implementing:
1. **Prioritize offline operation** - no external API calls
2. **Keep dependencies minimal** - this runs on phones
3. **Make it beautiful** - the tactical HUD should feel professional
4. **Test thoroughly** - this is a security tool, reliability matters
5. **Document everything** - users need to understand what they're seeing

The name "AlienSkull: Surveillance Killer" reflects the mission: using alien-like detection capabilities (RF scanning) to identify and neutralize surveillance threats (hence the skull - death to surveillance).

Remember: This is for **defensive security research only**. All functionality is passive scanning - we never transmit, inject, or attack.
