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

## File Structure & Declarative Profiles

Hardware profiles are defined declaratively in JSON format:
- **Built-in Profile**: `pipewire_config/profiles/babyface_pro.json`
- **User Custom Profiles**: `~/.config/pipewire-audio-config/profiles/*.json`

### Babyface Pro Hardware Mixer Layout

The profile defines comprehensive ALSA mixer controls:

#### 1. Input Controls (28 Channels)
- **Analog Preamps & Line Inputs**:
  - `Mic1 Gain` (`Mic-AN1 Gain`, 0–65 dB scaled)
  - `Mic1-L (AN1)` & `Mic1-R (AN2)` (`Mic-AN1-AN1`, `Mic-AN1-AN2`)
  - `Mic2 Gain` (`Mic-AN2 Gain`, 0–65 dB scaled)
  - `Mic2-L (AN1)` & `Mic2-R (AN2)` (`Mic-AN2-AN1`, `Mic-AN2-AN2`)
  - `Inst3 Gain` (`Line-IN3 Gain`, 0–18 dB scaled)
  - `Inst3-L (AN1)` & `Inst3-R (AN2)` (`Line-IN3-AN1`, `Line-IN3-AN2`)
  - `Inst4 Gain` (`Line-IN4 Gain`, 0–18 dB scaled)
  - `Inst4-L (AN1)` & `Inst4-R (AN2)` (`Line-IN4-AN1`, `Line-IN4-AN2`)
- **Digital S/PDIF Inputs**:
  - `S/PDIF-L (AS1/AN1)` & `S/PDIF-L (AS1/AN2)`
  - `S/PDIF-R (AS2/AN1)` & `S/PDIF-R (AS2/AN2)`
- **ADAT Optical Inputs**:
  - `ADAT1-L` through `ADAT6-R` (12 channels)

#### 2. Output Controls (11 Faders)
- **Coupled Stereo Main Analog Out**:
  - `Main (AN1/2)` (controls `Main-Out AN1` and `Main-Out AN2` simultaneously)
- **Headphone Outs**:
  - `Phones-L (PH3)` & `Phones-R (PH4)`
- **Digital S/PDIF Outs**:
  - `S/PDIF-L (AS1)` & `S/PDIF-R (AS2)`
- **ADAT Optical Outs**:
  - `ADAT1 (ADAT3)` through `ADAT6 (ADAT8)`

Each channel includes independent **Mute ("M")** and **Solo ("S")** routing.

## Adding More Devices

To add custom names or mixer controls for another device, place a JSON file in `~/.config/pipewire-audio-config/profiles/my_device.json`:

```json
{
  "name": "My Custom Audio Device",
  "match_description": "MyDevice",
  "channels": 8,
  "has_input_mixer": false,
  "has_output_mixer": false,
  "channel_names": {
    "outputs": ["Out-1", "Out-2", "Out-3", "Out-4", "Out-5", "Out-6", "Out-7", "Out-8"],
    "inputs": ["In-1", "In-2", "In-3", "In-4", "In-5", "In-6", "In-7", "In-8"]
  }
}
```

## Related Files

- `CHANNEL_LAYOUT.md` - Standard channel naming explanation
- `../README.md` - General project documentation
- `pipewire_config/profiles/babyface_pro.json` - Declarative JSON profile definition
