#!/data/data/com.termux/files/usr/bin/bash
# AlienSkull Installation Script for Termux
# Privacy-first surveillance detection system

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     █████╗ ██╗     ██╗███████╗███╗   ██╗███████╗██╗  ██╗║"
echo "║    ██╔══██╗██║     ██║██╔════╝████╗  ██║██╔════╝██║ ██╔╝║"
echo "║    ███████║██║     ██║█████╗  ██╔██╗ ██║███████╗█████╔╝ ║"
echo "║    ██╔══██║██║     ██║██╔══╝  ██║╚██╗██║╚════██║██╔═██╗ ║"
echo "║    ██║  ██║███████╗██║███████╗██║ ╚████║███████║██║  ██╗║"
echo "║    ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝║"
echo "║                                                           ║"
echo "║              SURVEILLANCE KILLER v1.0.0                   ║"
echo "║               Installation Script                         ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "[*] Starting AlienSkull installation..."
echo ""

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "[!] Error: This script must be run in Termux"
    echo "[!] Install Termux from F-Droid: https://f-droid.org/packages/com.termux/"
    exit 1
fi

echo "[1/8] Updating package lists..."
pkg update -y

echo ""
echo "[2/8] Installing system dependencies..."
pkg install -y python python-pip git termux-api

echo ""
echo "[!] IMPORTANT: Install Termux:API app from F-Droid"
echo "[!] URL: https://f-droid.org/packages/com.termux.api/"
echo "[!] Press Enter when Termux:API is installed..."
read

echo ""
echo "[3/8] Verifying Termux:API installation..."
if ! command -v termux-wifi-scaninfo &> /dev/null; then
    echo "[!] Warning: termux-wifi-scaninfo not found"
    echo "[!] Make sure Termux:API app is installed from F-Droid"
    echo "[!] Continue anyway? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
else
    echo "[✓] Termux:API detected"
fi

echo ""
echo "[4/8] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "[5/8] Creating directory structure..."
mkdir -p ~/.local/share/alienskull
mkdir -p ~/.config/alienskull

echo ""
echo "[6/8] Initializing configuration..."
if [ ! -f ~/.config/alienskull/config.json ]; then
    cat > ~/.config/alienskull/config.json << EOF
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
EOF
    echo "[✓] Created default configuration"
else
    echo "[✓] Configuration already exists"
fi

echo ""
echo "[7/8] Creating launcher script..."
cat > ~/alienskull << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# AlienSkull Launcher

cd ~/SurvellanceKiller || cd ~/alienskull
python3 server.py
EOF

chmod +x ~/alienskull

echo ""
echo "[8/8] Setting up permissions..."
echo ""
echo "[!] IMPORTANT: Grant the following permissions to Termux:"
echo "    - Location (for Wi-Fi scanning)"
echo "    - Nearby devices (for Bluetooth scanning)"
echo ""
echo "Press Enter to open app settings..."
read
termux-open-url "package:com.termux"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  Installation Complete!                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "To start AlienSkull:"
echo "  1. Run: ~/alienskull"
echo "     or: python3 server.py"
echo ""
echo "  2. Open browser to: http://127.0.0.1:5000"
echo ""
echo "Configuration file: ~/.config/alienskull/config.json"
echo "Database location: ~/.local/share/alienskull/scans.db"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "LEGAL NOTICE:"
echo "This tool is for educational and security research purposes only."
echo "Passive scanning only - no active attacks or packet injection."
echo "Users are responsible for compliance with local regulations."
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "[✓] Ready to hunt surveillance threats!"
echo ""
