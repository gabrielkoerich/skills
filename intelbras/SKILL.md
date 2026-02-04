---
name: intelbras
description: Monitor and control Intelbras alarm systems and cameras. Supports AMT series, Intelbras IFR alarms with HTTP API. Get status, arm/disarm, and check camera streams.
homepage: https://www.intelbras.com.br
---

# Intelbras Alarm & Camera Skill

Monitor and control Intelbras alarm systems and cameras via HTTP API.

## Setup

### 1. Environment Variables (Required for Credentials)

Create a `.env` file in the skill directory by copying `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```bash
# Alarm System Configuration
INTELBRAS_ALARM_HOST=192.168.1.100
INTELBRAS_ALARM_PORT=80
INTELBRAS_ALARM_USERNAME=admin
INTELBRAS_ALARM_PASSWORD=your_actual_alarm_password
INTELBRAS_ALARM_ENABLED=true

# DVR Configuration (for cameras)
INTELBRAS_DVR_HOST=192.168.1.200
INTELBRAS_DVR_PORT=80
INTELBRAS_DVR_RTSP_PORT=554
INTELBRAS_DVR_USERNAME=admin
INTELBRAS_DVR_PASSWORD=your_actual_dvr_password
```

**Security Note:** The `.env` file is git-ignored. Never commit credentials to the repository!

### 2. Camera Configuration

Create `data/config.json` with your camera layout:

```json
{
  "cameras": [
    {
      "name": "BACKLEFT",
      "channel": 1,
      "rtsp_subtype": 0
    },
    {
      "name": "BACKRIGHT",
      "channel": 2,
      "rtsp_subtype": 0
    }
  ]
}
```

### Common Intelbras Alarm IPs
- AMT 8000: `192.168.1.100`
- AMT 1000: `192.168.1.64`
- IFR 7001/9001: `192.168.1.200`

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `INTELBRAS_ALARM_HOST` | Alarm system IP address | 192.168.1.100 |
| `INTELBRAS_ALARM_PORT` | Alarm HTTP port | 80 |
| `INTELBRAS_ALARM_USERNAME` | Alarm username | admin |
| `INTELBRAS_ALARM_PASSWORD` | Alarm password | (required) |
| `INTELBRAS_ALARM_ENABLED` | Enable alarm features | true |
| `INTELBRAS_DVR_HOST` | DVR IP address | 192.168.1.200 |
| `INTELBRAS_DVR_PORT` | DVR HTTP port | 80 |
| `INTELBRAS_DVR_RTSP_PORT` | DVR RTSP port | 554 |
| `INTELBRAS_DVR_USERNAME` | DVR username | admin |
| `INTELBRAS_DVR_PASSWORD` | DVR password | (required) |

## Commands

| Command | Usage |
|---------|-------|
| Status | `scripts/status.sh` |
| Arm | `scripts/arm.sh` |
| Disarm | `scripts/disarm.sh` |
| Partial | `scripts/partial.sh` |
| Camera snapshot | `scripts/camera-snap.sh <camera_name>` |
| All camera snapshots | `scripts/cameras-snap.sh` |
| Test | `scripts/test-connection.sh` |

## Examples

```bash
# Check alarm status
./scripts/status.sh

# Arm the alarm
./scripts/arm.sh

# Take snapshot from CAM1 camera
./scripts/camera-snap.sh CAM1

# Take snapshots from all cameras
./scripts/cameras-snap.sh

# Test connection
./scripts/test-connection.sh
```

## Output Examples

```
=== Intelbras Alarm Status ===
Status: DESARMED (Disarmed)
Partitions: 1 armed
Zones: 32 total, 0 open

=== Camera Snapshot ===
BACKLEFT: media/cameras/BACKLEFT.jpg
```

## Notes
- Default port is 80 (HTTP)
- RTSP camera streams use port 554
- Some models support HTTPS on port 443
- Alarm may have rate limits - avoid rapid successive calls
- Camera snapshots require ffmpeg
- Credentials are read from environment variables first, then fall back to config file
