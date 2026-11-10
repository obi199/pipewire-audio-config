# Buffer Size Changes - How It Works

## Quick Answer
**Yes, you can change the buffer size**, but it requires restarting WirePlumber to take effect.

## What Is Buffer Size?

Buffer size (latency) is the amount of audio data held in memory at any time:
- **Smaller buffer** (32-128 samples) = Lower latency, more CPU load
- **Larger buffer** (512-4096 samples) = Higher latency, more stable

## How To Change Buffer Size

### Step 1: Open the GUI
```bash
cd ~/CLionProjects/pipewire-audio-config
./run-pipewire-config.sh
```

### Step 2: Select Device
1. Select your audio device from the dropdown (e.g., "Babyface Pro")
2. The current buffer size is shown in the "Device Information" section

### Step 3: Change Buffer Size
1. Find "Buffer Size (samples):" in the "Device Configuration" section
2. Click the dropdown and select a new size:
   - 32, 64, 128 = Low latency (more CPU usage)
   - 256, 512 = Balanced (recommended)
   - 1024, 2048, 4096 = High latency (most stable)
3. Hover over the dropdown to see tooltip with details

### Step 4: Save and Apply
**Option A: Save as Profile** (Recommended)
```
1. Click "Save as Profile"
2. Dialog appears with command to restart WirePlumber
3. Restart WirePlumber (see Step 5)
```

**Option B: Apply Configuration** (Quick test)
```
1. Click "Apply Configuration"
2. Shows current settings
3. Restart WirePlumber (see Step 5)
```

### Step 5: Restart WirePlumber
After changing buffer size, you MUST restart WirePlumber:

**Method 1: Command Line**
```bash
systemctl --user restart wireplumber
```

**Method 2: Restart PipeWire**
```bash
systemctl --user restart pipewire wireplumber
```

**Method 3: Complete PipeWire + PulseAudio Restart**
```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### Step 6: Verify
1. After restart, launch the GUI again
2. Select the same device
3. Check that buffer size is now set correctly
4. Test audio to confirm it works smoothly

## Important Notes

### Volume & Mute Changes
✅ **Take effect IMMEDIATELY** - No restart needed
- Volume slider changes
- Mute button changes
- Both apply instantly to PipeWire

### Device Configuration Changes
❌ **Require WirePlumber RESTART**:
- Buffer size changes
- Channel configuration
- Sample rate (if changed)
- ACP mode toggle

## What Gets Saved?

When you click "Save as Profile", the configuration is saved to:
- **Config file**: `~/.config/wireplumber/wireplumber.conf.d/50-device-*.conf`
  - Contains: channels, buffer size, ACP mode, channel positions
  - Loaded by WirePlumber on startup
- **Volume file**: `~/.config/wireplumber/wireplumber.conf.d/volume-*.json`
  - Contains: master volume, per-channel volumes, mute states
  - Loaded by the GUI on device selection

## Example: Changing Babyface Pro Buffer Size

### Current State
- Device: Babyface Pro
- Buffer Size: 256 samples (5.33ms @ 48kHz)
- Status: Working fine

### Change to Larger Buffer
1. Open GUI → Select Babyface Pro
2. Change buffer from 256 → 512 samples
3. Click "Save as Profile"
4. See message: "To apply changes, run: systemctl --user restart wireplumber"
5. Open terminal and run: `systemctl --user restart wireplumber`
6. Wait 2-3 seconds for WirePlumber to restart
7. Audio device reconnects with new buffer size

### Verify It Worked
1. Open GUI again
2. Select Babyface Pro
3. Check Device Information section
4. Buffer Size should now show: ~512 samples

## Troubleshooting

### Buffer Size Doesn't Change After Restart
**Problem**: Changed buffer size, restarted WirePlumber, but it's still the old size

**Solution**:
1. Check if config file was created:
   ```bash
   ls ~/.config/wireplumber/wireplumber.conf.d/50-device-*.conf
   ```
2. Verify content of config file has correct buffer size
3. Restart WirePlumber again
4. If still not working, check WirePlumber logs:
   ```bash
   journalctl -eu wireplumber --since "5 minutes ago"
   ```

### Audio Stops Working After Changing Buffer
**Problem**: Audio goes silent after changing buffer size

**Solution**:
1. Try restarting PipeWire completely:
   ```bash
   systemctl --user restart pipewire
   ```
2. Or reconnect the audio device (unplug and replug USB)
3. If problem persists, revert buffer size to previous value and restart

### "Cannot apply changes" Error
**Problem**: Get an error when clicking "Apply Configuration"

**Solution**:
1. Make sure device is selected (not "Scanning devices...")
2. Try closing and reopening the GUI
3. Check that PipeWire is running: `pgrep pipewire`

## Recommended Settings

### For Low Latency (Music Production, Live Performance)
- Buffer Size: 128 samples
- Restart needed? Yes (after first change only)
- Pros: Very responsive, minimal delay
- Cons: Higher CPU usage, may need powerful computer

### For Balanced (General Use)
- Buffer Size: 256 samples ← **DEFAULT & RECOMMENDED**
- Restart needed? Yes (after first change only)
- Pros: Good balance of latency and stability
- Cons: Slightly more latency than 128

### For Maximum Stability (Recording, Streaming)
- Buffer Size: 512-1024 samples
- Restart needed? Yes (after first change only)
- Pros: Very stable, low CPU usage
- Cons: Noticeable latency

## Technical Details

### How Buffer Size is Stored
In the WirePlumber config file (~/.config/wireplumber/wireplumber.conf.d/50-device-*.conf):
```
latency.internal.ns = 5333333  # 256 samples at 48kHz
```

Conversion formula:
```
nanoseconds = (samples / sample_rate) * 1,000,000,000
samples = (nanoseconds * sample_rate) / 1,000,000,000
```

### Hardware Buffer Control
Under the hood, PipeWire sets:
- `api.alsa.period-size` - Hardware buffer size
- `api.alsa.period-num` - Number of periods
- `api.alsa.headroom` - Extra buffer for stability

### WirePlumber Restart Process
When you restart WirePlumber:
1. WirePlumber service stops
2. All audio connections close temporarily
3. WirePlumber reloads config files from ~/.config/wireplumber/
4. Device properties updated from config
5. Audio reconnects automatically
6. Applications resume playback/recording

## See Also
- Buffer Size Reference: BUFFER_SIZE_REFERENCE.md
- Device Configuration: ../README.md
- PipeWire Documentation: https://docs.pipewire.org/

