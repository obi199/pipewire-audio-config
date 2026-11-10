# PipeWire Audio Buffer Size Reference

Standard buffer sizes used in audio production, with actual latency at different sample rates.

## Quick Reference Table

| Samples | @ 44.1kHz | @ 48kHz | @ 96kHz | Use Case |
|---------|-----------|---------|---------|----------|
| 32 | 0.73ms | 0.67ms | 0.33ms | Extreme low-latency (CPU intensive) |
| 64 | 1.45ms | 1.33ms | 0.67ms | Very low-latency monitoring |
| 128 | 2.90ms | 2.67ms | 1.33ms | Low-latency recording/plugin use |
| 256 | 5.80ms | 5.33ms | 2.67ms | **Balanced (recommended default)** |
| 512 | 11.61ms | 10.67ms | 5.33ms | Standard stable recording |
| 1024 | 23.22ms | 21.33ms | 10.67ms | High stability, streaming |
| 2048 | 46.44ms | 42.67ms | 21.33ms | Maximum stability |
| 4096 | 92.88ms | 85.33ms | 42.67ms | Very high stability, playback |

## For RME Babyface Pro

### Low-Latency Monitoring
```
Buffer: 64 samples
Sample Rate: 48kHz
Latency: 1.33ms
```

### Balanced Recording/Playback
```
Buffer: 256 samples (default)
Sample Rate: 48kHz
Latency: 5.33ms
```

### Professional/Studio Work
```
Buffer: 128 samples
Sample Rate: 96kHz
Latency: 1.33ms
Channels: 12
```

### Stable Streaming/Playback
```
Buffer: 512-1024 samples
Sample Rate: 48kHz
Latency: 10-21ms
```

## Calculation Formula

```
Latency (ms) = (Buffer Size in samples) / (Sample Rate in Hz) × 1000
```

### Examples:
- 256 samples @ 48kHz: 256 / 48000 × 1000 = **5.33ms**
- 128 samples @ 96kHz: 128 / 96000 × 1000 = **1.33ms**
- 1024 samples @ 44.1kHz: 1024 / 44100 × 1000 = **23.22ms**

## Which Buffer Size?

### If you hear audio dropouts or crackles
→ Increase buffer size (256 → 512 → 1024)

### If you need quick response (monitoring, games, live)
→ Decrease buffer size (256 → 128 → 64)

### If your CPU usage is high
→ Increase buffer size OR reduce plugins/tracks

### For starting out
→ Use **256 samples** and adjust from there

## CPU Impact

- **Smaller buffers** = Lower latency but higher CPU usage
- **Larger buffers** = Higher latency but lower CPU usage

Find the sweet spot where:
- No audio dropouts
- Latency is acceptable for your workflow
- CPU usage is comfortable
