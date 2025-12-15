# AlienSkull: Surveillance Killer 👽💀

**Transform your Android phone into a portable security audit device.**

AlienSkull is an open-source, privacy-first surveillance detection tool that runs entirely offline via Termux. It scans and visualizes nearby Wi-Fi networks and Bluetooth devices on a real-time tactical radar HUD, helping you identify potential surveillance risks and network security issues.

```
     █████╗ ██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗
    ██╔══██╗██║     ██║██╔════╝████╗  ██║██╔════╝██║ ██╔╝
    ███████║██║     ██║█████╗  ██╔██╗ ██║███████╗█████╔╝
    ██╔══██║██║     ██║██╔══╝  ██║╚██╗██║╚════██║██╔═██╗
    ██║  ██║███████╗██║███████╗██║ ╚████║███████║██║  ██╗
    ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

          SURVEILLANCE KILLER - Privacy First Defense
```

## 🌟 Features

### Core Capabilities
- **📡 Live Wi-Fi Scanning** - Real-time network detection with RSSI-based distance estimation
- **📱 BLE Device Detection** - Scan for Bluetooth Low Energy devices (trackers, beacons, etc.)
- **🎯 Tactical Radar HUD** - Satellite-style visualization with risk-based color coding
- **⚠️ Risk Scoring Engine** - Automatic threat assessment based on security type, signal strength, and behavior
- **📊 Intel Timeline** - Comprehensive scan history with export capabilities
- **🔒 Offline-First** - Zero cloud dependencies, no data leaks
- **🎨 Clean UI** - Dark tactical interface optimized for field use

### Security Analysis
- Detects open, WEP, WPA, WPA2, and WPA3 networks
- Identifies hidden SSIDs and suspicious network names
- Tracks known tracker devices (AirTags, Tiles, SmartTags)
- Real-time anomaly detection
- Signal strength analysis for proximity detection

## 🚀 Quick Start

### Prerequisites

1. **Android Phone** (Android 7.0+)
2. **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/)
3. **Termux:API** from [F-Droid](https://f-droid.org/packages/com.termux.api/)

> ⚠️ **Important:** Do NOT install Termux from Google Play Store. Use F-Droid only.

### Installation

1. **Install Termux and Termux:API from F-Droid**

2. **Clone the repository:**
   ```bash
   pkg install git
   git clone https://github.com/yourusername/alienskull.git
   cd alienskull
   ```

3. **Run the installation script:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

4. **Grant permissions:**
   - Location (for Wi-Fi scanning)
   - Nearby devices (for Bluetooth scanning)

5. **Start AlienSkull:**
   ```bash
   ~/alienskull
   # or
   python3 server.py
   ```

6. **Open in browser:**
   - Navigate to `http://127.0.0.1:5000`

## 📱 Usage

### Main Radar View

1. Click **"Start Scan"** to begin continuous scanning
2. Networks appear as dots on the radar based on distance and signal strength
3. Click any contact for detailed information
4. Color coding indicates risk level:
   - 🔵 **Cyan**: Low risk (secure networks)
   - 🟡 **Amber**: Medium risk (older security)
   - 🔴 **Red**: High risk (open/WEP networks)
   - 🟣 **Purple**: BLE devices

### Timeline View

- View historical scan data
- Filter by risk level and time range
- Export data to JSON or CSV
- View detailed network/device information

### Controls

- **Start Scan**: Begin continuous background scanning
- **Stop Scan**: Stop background scanning
- **Scan Once**: Perform single scan

## 🔧 Configuration

Configuration file: `~/.config/alienskull/config.json`

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
  "port": 5000,
  "host": "127.0.0.1"
}
```

### Configuration Options

- **scan_interval**: Time between scans in seconds (default: 5)
- **max_display_distance**: Maximum radar display range in meters (default: 100)
- **history_retention_days**: How long to keep scan history (default: 30)
- **ble_scanning**: Enable/disable Bluetooth scanning (default: true)
- **port**: Web server port (default: 5000)
- **host**: Web server host (default: 127.0.0.1)

## 📊 Risk Scoring

AlienSkull uses a comprehensive risk scoring algorithm:

### Security Type (0-50 points)
- **WEP**: +50 (critical - easily cracked)
- **Open**: +40 (no encryption)
- **WPA**: +20 (outdated)
- **WPA2**: +10 (standard)
- **WPA3**: +0 (secure)

### Signal Strength (0-30 points)
- **> -40 dBm**: +30 (< 5m - very suspicious)
- **> -60 dBm**: +15 (5-20m - close)
- **> -80 dBm**: +5 (20-50m - moderate)

### Anomalies (0-20 points)
- Hidden SSID: +20
- Suspicious name patterns: +10
- New network detected: +5

**Total Score**: 0-100 (capped)

### Risk Levels
- **0-29**: Minimal
- **30-59**: Low
- **60-79**: Medium
- **80-100**: High/Critical

## 🛡️ Privacy & Security

### Privacy First
- ✅ All data stored locally on device
- ✅ No network transmission of scan data
- ✅ No cloud dependencies
- ✅ No telemetry or analytics
- ✅ Optional MAC anonymization in exports

### Legal Compliance
- ✅ Passive scanning only (no packet injection)
- ✅ No active network attacks
- ✅ Educational/security research purposes
- ⚠️ User responsibility for legal use

### Code Security
- Input validation on all API calls
- SQL injection prevention (parameterized queries)
- XSS prevention in web UI
- No credential storage

## 📁 Project Structure

```
alienskull/
├── core/
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
├── templates/
│   ├── index.html          # Main radar view
│   └── timeline.html       # Scan history view
├── server.py               # Flask application
├── install.sh              # Installation script
├── requirements.txt        # Python dependencies
└── README.md
```

## 🔍 Troubleshooting

### "Termux API not found" error
- Install Termux:API app from F-Droid
- Install termux-api package: `pkg install termux-api`
- Grant location and Bluetooth permissions

### No networks detected
- Ensure location permission is granted
- Check if Wi-Fi is enabled on device
- Try `termux-wifi-scaninfo` manually to test

### BLE scanning not working
- Ensure Bluetooth is enabled
- Grant nearby devices permission
- Some devices may have limited BLE support

### Can't access web interface
- Make sure server is running: `python3 server.py`
- Try accessing `http://127.0.0.1:5000`
- Check firewall settings in Termux

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint recommended rules for JavaScript
- Write clear docstrings and comments
- Test on multiple Android versions if possible

## 📝 License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).

See [LICENSE](LICENSE) file for details.

## ⚖️ Legal Disclaimer

AlienSkull is provided for **educational and security research purposes only**.

- This tool performs passive scanning only
- No active network attacks or packet injection
- Users are responsible for compliance with local laws and regulations
- Unauthorized access to networks or devices is illegal
- Use responsibly and ethically

The developers assume no liability for misuse of this software.

## 🙏 Acknowledgments

- Built with ❤️ for the privacy and security community
- Powered by [Termux](https://termux.com/)
- Inspired by classic radar interfaces and tactical HUDs
- Special thanks to the open-source security tools community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/alienskull/issues)
- **Documentation**: This README and CLAUDE.md
- **Security**: Report security issues privately

## 🔮 Future Enhancements (v2.0 Roadmap)

- GPS integration for wardriving mode
- 3D visualization option
- Deauth detection
- Network mapping over time
- Machine learning for anomaly detection
- Multi-device collaborative scanning

---

**Death to surveillance. Long live privacy.** 👽💀

*Made with alien technology and open source love.*
