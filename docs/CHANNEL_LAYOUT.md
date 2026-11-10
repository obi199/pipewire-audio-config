# Channel Layout Reference

## Where Channel Names Come From

The channel names in the code (lines 313-320) follow **international audio standards**:

### Standards Used
1. **ALSA (Advanced Linux Sound Architecture)** - Linux audio standard
2. **PipeWire** - Modern Linux audio server (uses ALSA channel names)
3. **ITU-R BS.775** - International audio standard for surround sound

## Channel Abbreviations

| Code | Full Name | Position |
|------|-----------|----------|
| **FL** | Front Left | Left side at front |
| **FR** | Front Right | Right side at front |
| **FC** | Front Center | Center at front |
| **LFE** | Low Frequency Effects | Subwoofer (bass) |
| **RL** | Rear Left | Left side at back |
| **RR** | Rear Right | Right side at back |
| **SL** | Side Left | Left side (middle height) |
| **SR** | Side Right | Right side (middle height) |
| **FLC** | Front Left Center | Between front-left and center |
| **FRC** | Front Right Center | Between front-right and center |
| **RC** | Rear Center | Center at back |
| **TC** | Top Center | Center above listener |
| **TFL** | Top Front Left | Top-front-left corner |
| **TFR** | Top Front Right | Top-front-right corner |
| **TRL** | Top Rear Left | Top-back-left corner |
| **TRR** | Top Rear Right | Top-back-right corner |

## Current Channel Layouts in Our Tool

### 2 Channels (Stereo)
```
FL  FR
Left Right
```

### 4 Channels (Quad)
```
FL       FR
RL       RR
```

### 6 Channels (5.1 Surround)
```
FL   FC   FR
RL       RR
   (LFE - Subwoofer)
```

### 8 Channels (7.1 Surround)
```
FL   FC   FR
SL       SR
RL       RR
   (LFE - Subwoofer)
```

### 12 Channels (7.1 + ADAT)
```
FL  FLC  FC  FRC  FR
SL              SR
RL   RC       RR
     (LFE + TC)
```
This is what your **RME Babyface Pro** uses!

### 16 Channels (Full 3D Audio)
```
TFL  TC  TFR      (Top layer)
FL  FLC FC FRC FR  (Front layer)
SL           SR    (Side layer)
RL   RC       RR   (Rear layer)
TRL  TRR           (Bottom-rear)
     (LFE)
```

## ADAT Channels

ADAT (Alesis Digital Audio Tape) is a digital interface that carries **8 channels of audio**.

In your Babyface Pro configuration, the 12-channel layout is mapped as:
- **Channels 0-1**: FL, FR (main analog outputs)
- **Channels 2-9**: ADAT channels (mapped to FC, LFE, RL, RR, FLC, FRC, RC, SL, SR)
- **Channels 10-11**: SR, TC (side/top channels)

The actual physical routing depends on your Babyface Pro settings, but PipeWire presents them in this standard layout.

## How This Works in Code

```python
position_map = {
    2: '[ "FL", "FR" ]',
    12: '[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC" ]',
}
```

When you select 12 channels, the tool:
1. Looks up the position in `position_map`
2. Gets: `[ "FL", "FR", "FC", "LFE", "RL", "RR", "FLC", "FRC", "RC", "SL", "SR", "TC" ]`
3. Writes this to WirePlumber config as `audio.position`
4. PipeWire uses this to label the 12 channels

## Why These Names?

✅ **Standardized** - Same names across all Linux audio software
✅ **Compatible** - Professional audio tools use same names
✅ **Clear** - Immediately tell you channel purpose (front, rear, center, etc.)
✅ **Professional** - Used in movie/game studios worldwide

## Practical Example: Your Babyface Pro

When you open the GUI and select 12 channels, you see:
- In qpwgraph: ports labeled `playback_FL`, `playback_FR`, `capture_FC`, etc.
- In PipeWire: channels identified by these position names
- Your DAW sees: 12 discrete channels with clear labels

## Standards Reference

- **ALSA Standard**: Used by Linux audio for 30+ years
- **PipeWire Format**: Modern replacement, follows same naming
- **ITU-R BS.775**: International standard for surround sound
- **Dolby Digital**: 5.1, 7.1 formats use same channel positions

---

## For Different Devices

Not all devices support all 16 channels. Common limits:
- **USB Audio Class 1**: Usually 2, 4, or 6 channels
- **USB Audio Class 2**: Can do 2-32+ channels
- **RME Devices**: Professional, support 12+ channels
- **Babyface Pro**: 12 channels in Class Compliant Mode (what you have)

The position map in our tool can be extended to support more channels if needed!
