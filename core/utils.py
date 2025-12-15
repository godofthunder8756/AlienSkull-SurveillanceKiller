"""
Utility Functions - Distance calculation, MAC lookup, coordinate generation
"""

import math
import hashlib
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def rssi_to_distance(rssi: int, frequency: int = 2437) -> float:
    """
    Convert RSSI (signal strength) to estimated distance in meters
    Uses Free Space Path Loss formula

    Args:
        rssi: Received Signal Strength Indicator (dBm)
        frequency: Frequency in MHz (default 2437 MHz for channel 6)

    Returns:
        Estimated distance in meters
    """
    try:
        # Convert frequency to GHz
        freq_ghz = frequency / 1000.0

        # Free Space Path Loss formula
        # distance = 10 ^ ((27.55 - (20 * log10(freq)) + abs(RSSI)) / 20)
        if freq_ghz > 0:
            exponent = (27.55 - (20 * math.log10(freq_ghz)) + abs(rssi)) / 20
            distance = 10 ** exponent
        else:
            # Fallback for invalid frequency
            distance = 10 ** ((27.55 - (20 * math.log10(2.437)) + abs(rssi)) / 20)

        # Clamp to reasonable values (1cm to 1000m)
        return max(0.01, min(distance, 1000))

    except Exception as e:
        logger.warning(f"Error calculating distance from RSSI {rssi}: {e}")
        # Default fallback based on rough RSSI ranges
        if rssi > -40:
            return 1.0
        elif rssi > -60:
            return 10.0
        elif rssi > -80:
            return 50.0
        else:
            return 100.0


def mac_to_angle(mac: str) -> float:
    """
    Convert MAC address to consistent angle (0-360 degrees)
    Uses hash to ensure same MAC always appears at same angle

    Args:
        mac: MAC address string

    Returns:
        Angle in degrees (0-360)
    """
    try:
        # Hash the MAC address
        hash_value = int(hashlib.md5(mac.encode()).hexdigest(), 16)

        # Convert to angle 0-360
        angle = (hash_value % 360)

        return float(angle)

    except Exception as e:
        logger.warning(f"Error converting MAC to angle: {e}")
        return 0.0


def polar_to_cartesian(distance: float, angle: float) -> Tuple[float, float]:
    """
    Convert polar coordinates (distance, angle) to Cartesian (x, y)

    Args:
        distance: Distance from origin
        angle: Angle in degrees (0 = north, 90 = east)

    Returns:
        Tuple of (x, y) coordinates
    """
    # Convert angle to radians
    angle_rad = math.radians(angle)

    # Calculate Cartesian coordinates
    # Adjust angle so 0° is up (north)
    x = distance * math.sin(angle_rad)
    y = -distance * math.cos(angle_rad)

    return (x, y)


def calculate_radar_position(rssi: int, mac: str, frequency: int = 2437,
                            max_distance: float = 100.0) -> Dict[str, float]:
    """
    Calculate radar display position for a network/device

    Args:
        rssi: Signal strength
        mac: MAC/BSSID address
        frequency: Frequency in MHz
        max_distance: Maximum distance to display (meters)

    Returns:
        Dictionary with 'distance', 'angle', 'x', 'y'
    """
    # Calculate distance from RSSI
    distance = rssi_to_distance(rssi, frequency)

    # Cap distance at max display distance
    distance = min(distance, max_distance)

    # Calculate consistent angle from MAC
    angle = mac_to_angle(mac)

    # Convert to Cartesian coordinates
    x, y = polar_to_cartesian(distance, angle)

    return {
        'distance': round(distance, 2),
        'angle': round(angle, 2),
        'x': round(x, 2),
        'y': round(y, 2)
    }


def get_risk_color(risk_level: str) -> str:
    """
    Get HEX color code for risk level

    Args:
        risk_level: 'minimal', 'low', 'medium', 'high'

    Returns:
        HEX color code
    """
    colors = {
        'minimal': '#00f5ff',  # Cyan - safe
        'low': '#00f5ff',      # Cyan - safe
        'medium': '#ffba08',   # Amber - caution
        'high': '#ff0054',     # Red - danger
        'critical': '#ff0054'  # Red - danger
    }

    return colors.get(risk_level, '#00f5ff')


def get_device_icon(device_type: str) -> str:
    """
    Get icon/symbol for device type

    Args:
        device_type: Type of device

    Returns:
        Unicode symbol or emoji
    """
    icons = {
        'wifi': '📡',
        'ble': '📱',
        'tracker': '🏷️',
        'phone': '📱',
        'wearable': '⌚',
        'beacon': '📍',
        'audio': '🎧',
        'unknown': '❓'
    }

    device_lower = device_type.lower()

    for key, icon in icons.items():
        if key in device_lower:
            return icon

    return icons['unknown']


def format_mac_address(mac: str) -> str:
    """
    Format MAC address to standard format (XX:XX:XX:XX:XX:XX)

    Args:
        mac: MAC address in any format

    Returns:
        Formatted MAC address
    """
    try:
        # Remove common separators
        mac_clean = mac.replace(':', '').replace('-', '').replace('.', '').upper()

        # Ensure it's 12 characters
        if len(mac_clean) != 12:
            return mac  # Return original if invalid

        # Format with colons
        return ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])

    except Exception as e:
        logger.warning(f"Error formatting MAC address: {e}")
        return mac


def anonymize_mac(mac: str, keep_prefix: bool = True) -> str:
    """
    Anonymize MAC address for privacy

    Args:
        mac: MAC address
        keep_prefix: Keep OUI (first 3 octets) for vendor identification

    Returns:
        Anonymized MAC address
    """
    try:
        parts = mac.split(':')

        if keep_prefix and len(parts) >= 3:
            # Keep OUI, anonymize device part
            return ':'.join(parts[:3] + ['XX', 'XX', 'XX'])
        else:
            # Fully anonymize
            return 'XX:XX:XX:XX:XX:XX'

    except Exception as e:
        logger.warning(f"Error anonymizing MAC: {e}")
        return 'XX:XX:XX:XX:XX:XX'


def get_frequency_band(frequency: int) -> str:
    """
    Get frequency band name from frequency

    Args:
        frequency: Frequency in MHz

    Returns:
        Band name ('2.4 GHz', '5 GHz', etc.)
    """
    if 2400 <= frequency <= 2500:
        return '2.4 GHz'
    elif 5000 <= frequency <= 6000:
        return '5 GHz'
    elif frequency > 6000:
        return '6 GHz'
    else:
        return 'Unknown'


def calculate_signal_quality(rssi: int) -> Dict[str, any]:
    """
    Calculate signal quality metrics from RSSI

    Args:
        rssi: Signal strength in dBm

    Returns:
        Dictionary with quality percentage and description
    """
    # Convert RSSI to quality percentage (rough approximation)
    # Typical range: -90 dBm (poor) to -30 dBm (excellent)

    if rssi >= -40:
        quality_pct = 100
        description = 'Excellent'
    elif rssi >= -60:
        quality_pct = 70 + ((rssi + 60) * 1.5)
        description = 'Good'
    elif rssi >= -70:
        quality_pct = 50 + ((rssi + 70) * 2)
        description = 'Fair'
    elif rssi >= -80:
        quality_pct = 30 + ((rssi + 80) * 2)
        description = 'Weak'
    else:
        quality_pct = max(0, 30 + ((rssi + 80) * 0.5))
        description = 'Poor'

    return {
        'percentage': int(min(100, max(0, quality_pct))),
        'description': description,
        'rssi': rssi
    }


# MAC vendor lookup database (subset of common vendors)
# In production, use a full OUI database or API
MAC_VENDOR_DATABASE = {
    'AC:23:3F': 'Apple',
    '00:03:93': 'Apple',
    '00:50:F2': 'Microsoft',
    '38:FE:5E': 'Tile Inc.',
    'E4:04:39': 'Samsung',
    '00:A0:50': 'Cisco',
    '00:1B:63': 'Google',
    'B8:27:EB': 'Raspberry Pi Foundation',
    'DC:A6:32': 'Raspberry Pi Trading',
}


def lookup_mac_vendor(mac: str) -> Optional[str]:
    """
    Lookup device manufacturer from MAC address OUI

    Args:
        mac: MAC address

    Returns:
        Vendor name or None if not found
    """
    try:
        # Extract OUI (first 3 octets)
        oui = ':'.join(mac.split(':')[:3]).upper()

        return MAC_VENDOR_DATABASE.get(oui)

    except Exception as e:
        logger.warning(f"Error looking up MAC vendor: {e}")
        return None
