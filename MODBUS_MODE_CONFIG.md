# Modbus Mode Configuration Guide

## Overview
The Modbus Alarm Service supports two modes of operation:
1. **SIM Mode** - Connect to the Modbus Simulator (localhost:1502)
2. **REAL Mode** - Connect to the real Modbus device (192.168.1.100:502)

## Configuration

### How to Switch Modes

Edit `modbus_config.json` and change the `"mode"` setting:

```json
{
  "modbus": {
    "mode": "sim",
    ...
  }
}
```

### Available Modes

#### SIM Mode (Simulator)
```json
"mode": "sim"
```
- Connects to: `localhost:1502`
- Use when: Testing or developing without real hardware
- Requires: `modbus_simulator.py` running

#### REAL Mode (Real Hardware)
```json
"mode": "real"
```
- Connects to: `192.168.1.100:502`
- Use when: Running against real Modbus devices
- Requires: Real Modbus server available at configured address

## Configuration Structure

```json
{
  "modbus": {
    "mode": "sim",  // Change this: "sim" or "real"
    "hosts": {
      "sim": {
        "host": "localhost",
        "port": 1502
      },
      "real": {
        "host": "192.168.1.100",
        "port": 502
      }
    },
    "timeout": 3,
    "reconnect_delay": 0.1,
    "reconnect_delay_max": 300,
    "retries": 3
  },
  ...
}
```

## Running the System

### Step 1: Start the Modbus Server
If using SIM mode:
```bash
python modbus_simulator.py
```

### Step 2: Start the Alarm Service
```bash
python modbus_alarm_service.py
```

The service will automatically connect to the configured mode.

## Log Messages

When the service starts, you'll see a message indicating which mode is active:
- **SIM Mode:** `Modbus connected to localhost:1502 (SIM mode)`
- **REAL Mode:** `Modbus connected to 192.168.1.100:502 (REAL mode)`

## Customizing Host Addresses

To change the host addresses, edit the `hosts` section in `modbus_config.json`:

```json
"hosts": {
  "sim": {
    "host": "your.local.host",
    "port": 1502
  },
  "real": {
    "host": "192.168.x.x",
    "port": 502
  }
}
```

Then set `"mode"` to the desired one.
