# ACP Mode Explained

## What is ACP Mode?

**ACP** = **Advanced Channel Programming**

It's a setting that tells PipeWire how to configure USB audio devices, specifically controlling **which channels are exposed** to applications.

## The Core Problem ACP Solves

USB audio devices can support multiple **"alternate settings"** (different configurations). For example, the Babyface Pro has:

```
Altset 1: 2 channels (stereo only)
Altset 2: 12 channels (stereo + surround + ADAT)
```

**Without ACP mode**, PipeWire might not know which one to use.
**With ACP mode**, PipeWire uses special ALSA configuration to automatically select the best one.

## How It Works

### ACP Mode: ENABLED (True)

```
PipeWire Configuration
       ↓
api.alsa.use-acp = true
       ↓
Uses ALSA "ACP Driver" (specific driver for USB Audio Class devices)
       ↓
Automatically selects a LIMITED set of channels
       ↓
Usually: 2 channels ONLY (stereo)
       ↓
Result: Simple, compatible, but limited
```

**Effect:**
- Forces stereo-only operation
- Uses safest, most compatible configuration
- Works everywhere but loses multi-channel capability
- Good for: Basic audio, wide compatibility

### ACP Mode: DISABLED (False)

```
PipeWire Configuration
       ↓
api.alsa.use-acp = false
       ↓
Uses raw ALSA device access (direct hardware access)
       ↓
Exposes ALL available channels from the device
       ↓
Can use: 2, 4, 6, 8, 12, 16+ channels
       ↓
Result: Full capabilities, but requires manual setup
```

**Effect:**
- Exposes all device channels
- Enables multi-channel operation
- Requires proper configuration
- Good for: Professional audio, Babyface Pro, multi-channel work

## Visual Comparison

```
WITH ACP MODE (Enabled):
┌─────────────────────────────────┐
│  Babyface Pro Device            │
├─────────────────────────────────┤
│  • 12 channels available         │
│  • ACP mode: ENABLED            │
│           ↓                      │
│  Limited to: FL, FR (2 channels)│
│           ↓                      │
│  Applications see: 2 channels   │
│                                 │
│  ❌ ADAT channels hidden!       │
└─────────────────────────────────┘

WITHOUT ACP MODE (Disabled):
┌─────────────────────────────────┐
│  Babyface Pro Device            │
├─────────────────────────────────┤
│  • 12 channels available         │
│  • ACP mode: DISABLED           │
│           ↓                      │
│  Exposes all: FL, FR, FC, LFE...│
│           ↓                      │
│  Applications see: 12 channels  │
│                                 │
│  ✅ All channels including ADAT!│
└─────────────────────────────────┘
```

## For Your Babyface Pro

### Before (ACP Enabled)
```
Device: Babyface Pro
ACP Mode: Enabled
Channels visible: 2 (FL, FR only)
ADAT inputs: Hidden ❌
Problem: Could only use stereo
```

### After (ACP Disabled)
```
Device: Babyface Pro
ACP Mode: Disabled
Channels visible: 12 (Main + ADAT + S/PDIF)
ADAT inputs: Visible ✅
Benefit: Full multi-channel capability
```

## Where ACP Comes From

**ACP Mode** is part of the **ALSA Linux Sound Architecture**:

1. **ALSA USB Audio Class Driver** - Generic USB audio support
2. **ACP (Advanced Channel Programming)** - Special driver extension
3. Used specifically for **USB Audio Class devices** (cameras with audio, external sound cards, etc.)

## ACP vs Raw ALSA Mode

| Aspect | ACP Mode (Enabled) | Raw Mode (Disabled) |
|--------|------------------|-------------------|
| **Compatibility** | Maximum | Requires setup |
| **Channels** | Limited (usually 2) | All available |
| **Configuration** | Automatic | Manual |
| **ADAT Support** | ❌ No | ✅ Yes |
| **Professional Use** | ❌ Not ideal | ✅ Better |
| **Stability** | ✅ Very stable | ✅ Stable |
| **Latency** | Good | Better control |

## Why We Disabled It for Babyface Pro

Your Babyface Pro in **Class Compliant Mode** needs:
- Multiple channels (ADAT inputs)
- Raw ALSA device access
- Direct channel control

**Solution:** Disable ACP mode to unlock full capabilities

## What Happens When You Change ACP Mode

### Enabling ACP (True)
```
api.alsa.use-acp = true
↓
PipeWire: "Use ACP driver for this device"
↓
Channels: 2 (stereo only)
↓
Restart WirePlumber
↓
All multi-channel routing lost
```

### Disabling ACP (False)
```
api.alsa.use-acp = false
↓
PipeWire: "Use raw ALSA device access"
↓
Channels: 12 (or device maximum)
↓
Restart WirePlumber
↓
All channels become available
```

## In the GUI

When you see:

```
ACP Mode: Enabled (Stereo Only)
```
→ Device is limited to 2 channels

```
ACP Mode: Disabled (Full Channels)
```
→ Device exposes all available channels

The GUI shows this in the "Configuration" section:
```
ACP Mode (limits to stereo):
  ○ Disabled (Full Channels)  ← Recommended for Babyface Pro
  ● Enabled (Stereo Only)
```

## Common Scenarios

### Scenario 1: Built-in Laptop Audio
```
Device: HDA Intel
ACP Mode: Enabled (typical)
Channels: 2 (stereo)
Why: Built-in audio rarely needs multi-channel
```

### Scenario 2: RME Babyface Pro
```
Device: Babyface Pro
ACP Mode: Disabled (recommended)
Channels: 12 (main + ADAT + S/PDIF)
Why: Professional device, needs full channel access
```

### Scenario 3: USB Microphone
```
Device: USB Microphone
ACP Mode: Enabled (typical)
Channels: 1-2 (mono/stereo)
Why: Simple device, one channel per direction
```

## Technical Details

### ACP Driver Properties
- Developed for USB Audio Class 1 devices
- Automatically detects device capabilities
- Selects "sensible defaults" (usually stereo)
- Located in ALSA plugin: `usbstream`

### Raw Mode Properties
- Direct hardware access via ALSA
- No automatic channel limiting
- Requires explicit configuration
- More flexibility, less automatic

## Troubleshooting

### If channels disappear after changing ACP Mode
1. **Stop WirePlumber**: `systemctl --user stop wireplumber`
2. **Restart it**: `systemctl --user start wireplumber`
3. **Or**: Disconnect and reconnect the device

### If you want to switch modes
1. Open GUI
2. Change ACP Mode toggle
3. Click "Save as Profile"
4. Restart WirePlumber: `systemctl --user restart wireplumber`
5. Reconnect device

## Key Takeaway

```
┌─────────────────────────────────────────────┐
│ ACP MODE controls HOW channels are exposed │
│                                             │
│ ENABLED:  Limited channels (simple)        │
│ DISABLED: Full channels (professional)     │
│                                             │
│ For Babyface Pro → DISABLE for 12 channels│
└─────────────────────────────────────────────┘
```

## Related Configuration

ACP Mode works alongside:
- `api.alsa.use-chmap` - Channel mapping configuration
- `api.alsa.path` - Which ALSA device to use (hw:X)
- `audio.channels` - Number of channels to expose
- `audio.position` - How channels are labeled

All these work together to determine what the device looks like to applications.
