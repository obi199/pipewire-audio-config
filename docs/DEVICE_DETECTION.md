# How Device Detection Works

## Overview

The GUI uses a **three-step process** to detect and identify audio devices:

```
Step 1: Run pw-dump command
        ↓
Step 2: Parse JSON output
        ↓
Step 3: Extract device information
        ↓
Step 4: Display in GUI
```

## Step 1: Getting Raw Device Data

### Command Used
```bash
pw-dump
```

**What it does:**
- Queries the PipeWire audio server
- Returns **all PipeWire objects** as JSON data
- Includes devices, nodes, ports, modules, etc.

**Example output (truncated):**
```json
[
  {
    "id": 60,
    "type": "PipeWire:Interface:Node",
    "version": 3,
    "info": {
      "props": {
        "node.name": "alsa_output.usb-RME_Babyface_Pro__73045465__2A168CEA30AA1E8-00.analog-stereo",
        "node.description": "Babyface Pro (Class Compliant Mode) Analoges Stereo",
        "media.class": "Audio/Sink",
        "audio.channels": 12,
        "audio.rate": 48000,
        "api.alsa.path": "hw:1",
        ...
      }
    }
  },
  ...
]
```

## Step 2: Running in Background Thread

### Why Background Thread?

The detection runs in a **separate thread** (`DeviceDetector`) to avoid freezing the GUI:

```python
class DeviceDetector(QThread):
    def run(self):
        result = subprocess.run(['pw-dump'], ...)
        devices = self._parse_devices(result.stdout)
        self.devices_found.emit(devices)
```

**Benefits:**
- GUI stays responsive while scanning
- User can see "Scanning devices..." message
- Won't freeze if PipeWire takes time to respond

## Step 3: Parsing JSON Output

### Filtering Logic

The code filters through all PipeWire objects using **3 conditions**:

```python
# Condition 1: Must be a Node (not a port, link, or module)
if obj.get('type') == 'PipeWire:Interface:Node':
    
    # Condition 2: Must be ALSA device (not Bluetooth, JACK, etc.)
    if 'alsa' not in props.get('node.name', ''):
        continue
    
    # Condition 3: Must be audio input or output
    media_class = props.get('media.class', '')
    if media_class not in ['Audio/Sink', 'Audio/Source']:
        continue
```

### What Gets Extracted

For each device that passes filtering, the code extracts:

```python
device = {
    'id': 60,                          # PipeWire object ID
    'name': 'alsa_output.usb-RME...',  # Technical name
    'description': 'Babyface Pro...',  # Human-readable name ← This is what user sees
    'media_class': 'Audio/Sink',       # Output or Input?
    'channels': 12,                    # Number of channels
    'rate': 48000,                     # Sample rate
    'alsa_path': 'hw:1',               # ALSA device path
    'use_acp': False,                  # ACP mode enabled?
    'position': [...],                 # Channel positions (FL, FR, etc.)
    'latency_ns': 0,                   # Latency in nanoseconds
}
```

## Step 4: Display in GUI

### Device Dropdown Population

```python
for device in devices:
    # Add icon and description to dropdown
    icon = "🔊" if device['media_class'] == 'Audio/Sink' else "🎤"
    label = f"{icon} {device['description']}"
    self.device_combo.addItem(label, device)
```

**Result in GUI:**
```
🔊 Babyface Pro (Class Compliant Mode) Analoges Stereo
🎤 Babyface Pro (Class Compliant Mode) Analoges Stereo
```

## Device Detection Flow Diagram

```
┌─────────────────────────────────────────────┐
│      GUI Starts / Refresh Button Clicked    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Create DeviceDetector Thread             │
│    (Background process)                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Execute: pw-dump                         │
│    (Query PipeWire audio server)            │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Parse JSON Response                      │
│    Extract all PipeWire objects             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Filter Objects:                          │
│    ✓ Type = "PipeWire:Interface:Node"       │
│    ✓ Contains "alsa" in name                │
│    ✓ media.class = Audio/Sink or Source     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Extract Device Information:              │
│    • name, description, channels            │
│    • sample rate, ALSA path                 │
│    • channel positions, latency             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Emit Signal: devices_found               │
│    (Send results back to main thread)       │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Update GUI Dropdown:                     │
│    • Add each device with icon              │
│    • Store full device data                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    User Selects Device                      │
│    → on_device_changed() triggered          │
│    → update_device_info() displays details  │
└─────────────────────────────────────────────┘
```

## Custom Device Detection

After a device is detected, the code checks for **custom channel names**:

```python
def _get_device_channel_names(self, device_description, direction='outputs'):
    # Check if device matches any known device in DEVICE_CHANNEL_NAMES
    for device_key, device_config in DEVICE_CHANNEL_NAMES.items():
        if device_key.lower() in device_description.lower():
            return device_config['layout'].get(direction, [])
    return None
```

**How it works:**
1. Gets device description (e.g., "Babyface Pro (Class Compliant Mode)")
2. Checks if "Babyface Pro" is in DEVICE_CHANNEL_NAMES dictionary
3. If found, returns custom names (Main-L, ADAT-1, etc.)
4. Displays them in device info

## Device Properties Available

### From PipeWire (via pw-dump)

| Property | Example | Purpose |
|----------|---------|---------|
| `node.name` | `alsa_output.usb-RME...` | Technical identifier |
| `node.description` | `Babyface Pro...` | User-friendly name |
| `media.class` | `Audio/Sink` | Output or Input |
| `audio.channels` | `12` | Number of channels |
| `audio.rate` | `48000` | Sample rate in Hz |
| `api.alsa.path` | `hw:1` | ALSA device path |
| `audio.position` | `[FL, FR, ...]` | Channel layout |
| `latency.internal.ns` | `0` | Latency in nanoseconds |
| `api.alsa.use-acp` | `false` | ACP mode enabled |

## How Device Matching Works

### For Custom Names (Babyface Pro)

```python
# In DEVICE_CHANNEL_NAMES dictionary:
"Babyface Pro": {
    "name": "RME Babyface Pro - Physical I/O",
    "channels": 12,
    "layout": { ... }
}

# When device is detected:
device_description = "Babyface Pro (Class Compliant Mode) Analoges Stereo"

# Check if "Babyface Pro" (key) is in description:
if "babyface pro" in device_description.lower():
    # ✅ MATCH FOUND!
    # Use custom channel names
```

## Real-World Example

### 1. User Starts Application
```
GUI: "Scanning devices..."
```

### 2. DeviceDetector Runs pw-dump
```bash
$ pw-dump
[
  { "id": 60, "type": "PipeWire:Interface:Node", ... },
  { "id": 61, "type": "PipeWire:Interface:Node", ... },
  ...hundreds of objects...
]
```

### 3. Code Filters the Results
```
Processing object id=60:
  ✓ type = "PipeWire:Interface:Node" ✓
  ✓ "alsa" in "alsa_output.usb-RME..." ✓
  ✓ media_class = "Audio/Sink" ✓
  → ADD TO DEVICES LIST

Processing object id=100:
  ✓ type = "PipeWire:Interface:Node" ✓
  ✗ "alsa" not in "bluez_input...." ✗
  → SKIP (Bluetooth device)
```

### 4. GUI Updates
```
Device Dropdown:
  🔊 Babyface Pro (Class Compliant Mode) Analoges Stereo
  🎤 Babyface Pro (Class Compliant Mode) Analoges Stereo
```

### 5. User Selects Device
```
Device Information:
  Channels: 12
  Sample Rate: 48000 Hz
  Channel Layout: FL, FR, FC, LFE, RL, RR, FLC, FRC, RC, SL, SR, TC
  Custom Names: Main-L, Main-R, ADAT-1, ADAT-2, ...
```

## Why This Approach Works

✅ **Automatic** - No manual configuration needed
✅ **Fast** - Background thread keeps GUI responsive
✅ **Accurate** - Uses official PipeWire API (pw-dump)
✅ **Flexible** - Easy to add new device-specific names
✅ **Standards-Based** - Uses PipeWire metadata format
✅ **Reliable** - Filters by type and class to avoid false matches

## Adding More Devices

To auto-detect a new device with custom names:

```python
DEVICE_CHANNEL_NAMES = {
    "Babyface Pro": { ... },
    "Your Device": {
        "name": "Your Device Name",
        "channels": 8,
        "layout": {
            "outputs": ["Out-1", "Out-2", ...],
            "inputs": ["In-1", "In-2", ...]
        }
    }
}
```

The detection will automatically match and show custom names!

## Command Line Alternative

To see all detected devices manually:

```bash
# Get all audio devices
pw-dump | grep -i "media.class.*Audio"

# Get device details
pw-cli list-objects Node | grep -i alsa

# See full raw data
pw-dump | jq '.[] | select(.type | contains("Node"))'
```
