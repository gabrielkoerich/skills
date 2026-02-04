#!/usr/bin/env python3
"""Intelbras Alarm and Camera Controller - DVR Edition."""
import sys
import json
import os
import urllib.request
import base64
import subprocess
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
MEDIA_DIR = os.path.expanduser("~/.claude/media/cameras")

def load_config():
    """Load configuration from config.json and environment variables.
    
    Environment variables take precedence over config file values:
    - INTELBRAS_ALARM_HOST
    - INTELBRAS_ALARM_PORT
    - INTELBRAS_ALARM_USERNAME
    - INTELBRAS_ALARM_PASSWORD
    - INTELBRAS_ALARM_ENABLED
    - INTELBRAS_DVR_HOST
    - INTELBRAS_DVR_PORT
    - INTELBRAS_DVR_RTSP_PORT
    - INTELBRAS_DVR_USERNAME
    - INTELBRAS_DVR_PASSWORD
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Config file not found: {CONFIG_FILE}")
        print("Please create the config file with alarm and camera settings.")
        sys.exit(1)
    
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        
        # Apply environment variable overrides for alarm config
        alarm = config.get("alarm", {})
        alarm["host"] = os.getenv("INTELBRAS_ALARM_HOST", alarm.get("host", "192.168.1.100"))
        alarm["port"] = int(os.getenv("INTELBRAS_ALARM_PORT", alarm.get("port", 80)))
        alarm["username"] = os.getenv("INTELBRAS_ALARM_USERNAME", alarm.get("username", "admin"))
        alarm["password"] = os.getenv("INTELBRAS_ALARM_PASSWORD", alarm.get("password", ""))
        alarm["enabled"] = os.getenv("INTELBRAS_ALARM_ENABLED", str(alarm.get("enabled", True))).lower() == "true"
        config["alarm"] = alarm
        
        # Apply environment variable overrides for DVR config
        dvr = config.get("dvr", {})
        dvr["host"] = os.getenv("INTELBRAS_DVR_HOST", dvr.get("host", "192.168.1.200"))
        dvr["port"] = int(os.getenv("INTELBRAS_DVR_PORT", dvr.get("port", 80)))
        dvr["rtsp_port"] = int(os.getenv("INTELBRAS_DVR_RTSP_PORT", dvr.get("rtsp_port", 554)))
        dvr["username"] = os.getenv("INTELBRAS_DVR_USERNAME", dvr.get("username", "admin"))
        dvr["password"] = os.getenv("INTELBRAS_DVR_PASSWORD", dvr.get("password", ""))
        config["dvr"] = dvr
        
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

def get_auth_header(username, password):
    """Create basic auth header."""
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def check_alarm_status(config):
    """Check alarm system status."""
    alarm = config.get("alarm", {})
    if not alarm.get("enabled", True):
        print("⚠️ Alarm is disabled in config")
        return
    
    host = alarm.get("host", "192.168.1.100")
    port = alarm.get("port", 80)
    username = alarm.get("username", "admin")
    password = alarm.get("password", "")
    
    url = f"http://{host}:{port}/status.cgi"
    headers = get_auth_header(username, password)
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print("=== Intelbras Alarm Status ===")
            print(f"Status: {data.get('status', 'UNKNOWN')}")
            print(f"Partitions: {data.get('partitions', 'N/A')}")
            print(f"Zones: {data.get('zones', 'N/A')}")
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        print("Make sure the alarm system is reachable at the configured IP.")

def send_alarm_command(config, command):
    """Send command to alarm (arm/disarm/partial)."""
    alarm = config.get("alarm", {})
    if not alarm.get("enabled", True):
        print("⚠️ Alarm is disabled in config")
        return
    
    host = alarm.get("host", "192.168.1.100")
    port = alarm.get("port", 80)
    username = alarm.get("username", "admin")
    password = alarm.get("password", "")
    
    commands = {
        "arm": "arm",
        "disarm": "disarm", 
        "partial": "partial"
    }
    
    command_url = commands.get(command.lower())
    if not command_url:
        print(f"❌ Unknown command: {command}")
        return
    
    url = f"http://{host}:{port}/control.cgi?command={command_url}"
    headers = get_auth_header(username, password)
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print(f"✅ Alarm command sent: {command.upper()}")
            else:
                print(f"❌ Command failed: {response.status}")
    except Exception as e:
        print(f"❌ Error sending command: {e}")

def camera_snapshot(config, camera_name):
    """Take a snapshot from a DVR-based camera."""
    cameras = config.get("cameras", [])
    
    camera = None
    for cam in cameras:
        if cam.get("name", "").upper() == camera_name.upper():
            camera = cam
            break
    
    if not camera:
        print(f"❌ Camera not found: {camera_name}")
        print(f"Available cameras: {[c['name'] for c in cameras]}")
        return
    
    dvr = config.get("dvr", {})
    dvr_host = dvr.get("host", "192.168.1.200")
    dvr_rtsp_port = dvr.get("rtsp_port", 554)
    dvr_username = dvr.get("username", "admin")
    dvr_password = dvr.get("password", "")
    
    channel = camera.get("channel", 1)
    subtype = camera.get("rtsp_subtype", 0)
    
    # Build RTSP URL for DVR-based camera
    # Intelbras DVR format: rtsp://host:554/cam/realmonitor?channel=X&subtype=Y
    rtsp_url = f"rtsp://{dvr_host}:{dvr_rtsp_port}/cam/realmonitor?channel={channel}&subtype={subtype}"
    
    os.makedirs(MEDIA_DIR, exist_ok=True)
    output_file = os.path.join(MEDIA_DIR, f"{camera_name}.jpg")
    
    # Build ffmpeg command with auth if needed
    if dvr_username and dvr_password:
        rtsp_url_with_auth = f"rtsp://{dvr_username}:{dvr_password}@{dvr_host}:{dvr_rtsp_port}/cam/realmonitor?channel={channel}&subtype={subtype}"
    else:
        rtsp_url_with_auth = rtsp_url
    
    print(f"📷 Capturing {camera_name} from channel {channel}...")
    
    cmd = [
        "ffmpeg", "-y",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url_with_auth,
        "-vframes", "1",
        "-q:v", "2",
        output_file
    ]
    
    try:
        result = subprocess.run(cmd, timeout=30, capture_output=True)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"✅ {camera_name}: {output_file}")
        else:
            print(f"❌ Failed to capture {camera_name}")
            if result.stderr:
                error_lines = result.stderr.decode()[-500:]
                print(f"Error: {error_lines}")
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout capturing {camera_name}")
    except Exception as e:
        print(f"❌ Error capturing {camera_name}: {e}")

def all_cameras_snap(config):
    """Take snapshots from all cameras."""
    cameras = config.get("cameras", [])
    if not cameras:
        print("❌ No cameras configured")
        return
    
    print("=== Capturing all cameras from DVR ===")
    for camera in cameras:
        camera_snapshot(config, camera.get("name", ""))
    print("=== Done ===")

def test_connection(config):
    """Test connection to alarm system."""
    alarm = config.get("alarm", {})
    dvr = config.get("dvr", {})
    
    # Test DVR connection
    dvr_host = dvr.get("host", "192.168.1.200")
    print(f"=== Testing DVR connection at {dvr_host} ===")
    
    # Try HTTP first
    try:
        url = f"http://{dvr_host}/"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"✅ DVR HTTP accessible! Status: {response.status}")
    except Exception as e:
        if hasattr(e, 'reason'):
            print(f"⚠️ DVR HTTP not accessible: {e.reason}")
        else:
            print(f"⚠️ DVR HTTP not accessible: {e}")
    
    # Test RTSP port
    import socket
    dvr_port = dvr.get("rtsp_port", 554)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((dvr_host, dvr_port))
    sock.close()
    
    if result == 0:
        print(f"✅ DVR RTSP port ({dvr_port}) is open")
    else:
        print(f"⚠️ DVR RTSP port ({dvr_port}) is closed")

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: intelbras-alarm.py <command> [args]")
        print("Commands: status, arm, disarm, partial, snap <camera>, all-snap, test")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    config = load_config()
    
    if command == "status":
        check_alarm_status(config)
    elif command in ["arm", "disarm", "partial"]:
        send_alarm_command(config, command)
    elif command == "snap" and len(sys.argv) > 2:
        camera_snapshot(config, sys.argv[2])
    elif command == "all-snap":
        all_cameras_snap(config)
    elif command == "test":
        test_connection(config)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
