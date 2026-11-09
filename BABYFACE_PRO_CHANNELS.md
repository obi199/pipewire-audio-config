# Custom Channel Names for RME Babyface Pro

## Overview

Instead of generic surround sound labels (FL, FR, FC, etc.), the Babyface Pro now uses **meaningful physical I/O names** that reflect the actual connectors and functions.

## Physical Layout of Babyface Pro

### Outputs (12 channels total)
```
Channel 0-1:   Main Analog Out (XLR Balanced)
               • Left (Main-L)
               • Right (Main-R)

Channel 2-9:   ADAT Out (Optical ADAT connector) - 8 channels
               • ADAT-1 through ADAT-8

Channel 10-11: S/PDIF Digital Out (Coaxial)
               • S/PDIF-L (Digital Left)
               • S/PDIF-R (Digital Right)
```

### Inputs (12 channels total)
```
Channel 0-1:   Main Analog In (XLR Balanced)
               • Left (Main-L)
               • Right (Main-R)

Channel 2-9:   ADAT In (Optical ADAT connector) - 8 channels
               • ADAT-1 through ADAT-8

Channel 10-11: S/PDIF Digital In (Coaxial)
               • S/PDIF-L (Digital Left)
               • S/PDIF-R (Digital Right)
```

## Channel Name Mapping

| Index | Standard Name | Babyface Name | Physical Connection |
|-------|---------------|---------------|---------------------|
| 0 | FL (Front Left) | Main-L | XLR Analog Out/In Left |
| 1 | FR (Front Right) | Main-R | XLR Analog Out/In Right |
| 2 | FC (Front Center) | ADAT-1 | ADAT Optical 1 |
| 3 | LFE (Low Freq Effects) | ADAT-2 | ADAT Optical 2 |
| 4 | RL (Rear Left) | ADAT-3 | ADAT Optical 3 |
| 5 | RR (Rear Right) | ADAT-4 | ADAT Optical 4 |
| 6 | FLC (Front Left Center) | ADAT-5 | ADAT Optical 5 |
| 7 | FRC (Front Right Center) | ADAT-6 | ADAT Optical 6 |
| 8 | RC (Rear Center) | ADAT-7 | ADAT Optical 7 |
| 9 | SL (Side Left) | ADAT-8 | ADAT Optical 8 |
| 10 | SR (Side Right) | S/PDIF-L | S/PDIF Coaxial Left |
| 11 | TC (Top Center) | S/PDIF-R | S/PDIF Coaxial Right |

## How It Works

### In the GUI

When you select the Babyface Pro device, you'll see:

```
Device Information:
  Channels: 12
  Sample Rate: 48000 Hz
  Channel Layout: FL, FR, FC, LFE, RL, RR, FLC, FRC, RC, SL, SR, TC
  Custom Names: Main-L, Main-R, ADAT-1, ADAT-2, ADAT-3, ADAT-4, 
                ADAT-5, ADAT-6, ADAT-7, ADAT-8, S/PDIF-L, S/PDIF-R
```

### In PipeWire

When the config is applied:
- PipeWire still uses the standard names internally (FL, FR, etc.)
- But DAWs and applications see the friendly names (Main-L, ADAT-1, etc.)
- Makes routing much clearer when working with 12 channels

### In Your DAW

Applications that read PipeWire metadata will display:
```
Track 1: Main-L
Track 2: Main-R
Track 3: ADAT-1
Track 4: ADAT-2
...and so on
```

## File Structure

- **pipewire-device-config.py**: Main GUI (includes `DEVICE_CHANNEL_NAMES` mapping)
- **babyface_channels.py**: Extended channel mapping definitions (for future expansion)

## Adding More Devices

To add custom names for another device, edit `DEVICE_CHANNEL_NAMES` in `pipewire-device-config.py`:

```python
DEVICE_CHANNEL_NAMES = {
    "Babyface Pro": { ... },
    "Your Device Name": {
        "name": "Your Device - Custom Names",
        "channels": 8,
        "layout": {
            "outputs": ["Out-1", "Out-2", ...],
            "inputs": ["In-1", "In-2", ...]
        }
    }
}
```

## Advanced: Alternative Naming Schemes

See `babyface_channels.py` for alternative naming options:

1. **Simple Names** (default)
   - `Main-L`, `Main-R`, `ADAT-1`, etc.
   - Clear what each channel does

2. **Studio Names**
   - `Mic-In-L`, `Line-1`, `Drums-1`, etc.
   - Organized by function/purpose

3. **Technical Names**
   - `XLR-Out-L`, `ADAT-Out-1`, `Coax-Out-R`, etc.
   - Specific technical details

## Advantage over Standard Names

### Before (Generic Names)
```
FL, FR, FC, LFE, RL, RR, FLC, FRC, RC, SL, SR, TC
```
❌ Not immediately clear which are ADAT vs main outputs
❌ Confusing - looks like surround sound, not multi-interface setup

### After (Device-Specific Names)
```
Main-L, Main-R, ADAT-1, ADAT-2, ..., ADAT-8, S/PDIF-L, S/PDIF-R
```
✅ Immediately clear which connector each channel uses
✅ Perfect for professional setups with multiple interfaces
✅ No confusion about physical I/O routing

## Related Files

- `CHANNEL_LAYOUT.md` - Standard channel naming explanation
- `README.md` - General project documentation
- `pipewire-device-config.py` - Main application with mappings
