#!/usr/bin/env python3
"""
Audio analysis for speed verification.
Attempts: spectrogram, dominant frequency tracking, amplitude envelope (impact detection).
Limitation: Dashcam audio is typically low-fidelity monaural with heavy wind noise.
Expectation: Likely inconclusive for precise speed, but may reveal rhythmic patterns.
"""

import numpy as np
import wave
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal

# Load audio
wf = wave.open('outputs/audio.wav', 'rb')
rate = wf.getframerate()
frames = wf.readframes(wf.getnframes())
audio = np.frombuffer(frames, dtype=np.int16) / 32768.0
wf.close()

print(f'Audio: {len(audio)} samples at {rate} Hz, duration={len(audio)/rate:.2f}s')
print(f'Mean amplitude: {np.mean(np.abs(audio)):.4f}')
print(f'Peak: {np.max(np.abs(audio)):.4f}')

# --- Spectrogram (3-16 s window) ---
start_s, end_s = 3, 16
start_sample = int(start_s * rate)
end_sample = int(end_s * rate)
seg = audio[start_sample:end_sample]

fig, axes = plt.subplots(2, 1, figsize=(14, 8))

t = np.arange(len(seg)) / rate + start_s
axes[0].plot(t, seg, alpha=0.5, linewidth=0.1, color='steelblue')
axes[0].axhline(0, color='gray', linestyle='-', alpha=0.3)
axes[0].set_xlabel('Time (s)')
axes[0].set_ylabel('Amplitude')
axes[0].set_title(f'Audio Waveform ({start_s}-{end_s} s)')
axes[0].set_xlim([start_s, end_s])

f, t_spec, Sxx = signal.spectrogram(seg, rate, nperseg=2048, noverlap=1024)
axes[1].pcolormesh(t_spec + start_s, f, 10*np.log10(Sxx + 1e-10), shading='gouraud', cmap='magma')
axes[1].set_ylim([0, 6000])
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Frequency (Hz)')
axes[1].set_title('Spectrogram (3-16 s, 0-6000 Hz)')

plt.tight_layout()
plt.savefig('outputs/audio_analysis.png', dpi=150, bbox_inches='tight')
print('Saved: outputs/audio_analysis.png')

# --- Dominant frequency in road-noise band (500-3000 Hz) ---
noise_band = (f >= 500) & (f <= 3000)
Sxx_noise = Sxx[noise_band, :]
f_noise = f[noise_band]
max_freq_idx = np.argmax(Sxx_noise, axis=0)
max_freq = f_noise[max_freq_idx]
max_power = np.max(Sxx_noise, axis=0)

fig2, ax = plt.subplots(figsize=(14, 4))
ax.plot(t_spec + start_s, max_freq, 'o-', markersize=2, alpha=0.7, color='darkred')
ax.set_ylim([0, 3000])
ax.set_xlabel('Time (s)')
ax.set_ylabel('Dominant Frequency (Hz)')
ax.set_title('Dominant frequency in 500-3000 Hz band (road/tire noise hypothesis)')
ax.axhline(1000, color='gray', linestyle='--', alpha=0.5, label='1 kHz ref')
ax.legend()
plt.tight_layout()
plt.savefig('outputs/audio_dominant_freq.png', dpi=150, bbox_inches='tight')
print('Saved: outputs/audio_dominant_freq.png')

# --- Amplitude envelope (potential rhythmic impacts like guard rails) ---
analytic = signal.hilbert(seg)
envelope = np.abs(analytic)
env_ds = envelope[::160]
t_env = t[::160]

fig3, ax = plt.subplots(figsize=(14, 4))
ax.plot(t_env, env_ds, alpha=0.7, color='purple')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Envelope Amplitude')
ax.set_title('Amplitude Envelope (3-16 s)')
plt.tight_layout()
plt.savefig('outputs/audio_envelope.png', dpi=150, bbox_inches='tight')
print('Saved: outputs/audio_envelope.png')

# --- Try to detect peaks in envelope (potential periodic impacts) ---
# Smooth slightly
env_smooth = signal.savgol_filter(env_ds, 11, 2)
peaks, props = signal.find_peaks(env_smooth, distance=rate//10, prominence=0.001)
print(f'Envelope peaks detected: {len(peaks)}')
if len(peaks) >= 2:
    peak_times = t_env[peaks]
    intervals = np.diff(peak_times)
    print(f'Peak interval mean: {np.mean(intervals):.3f}s, std: {np.std(intervals):.3f}s')
    print(f'Resonant frequency hint: ~{1/np.mean(intervals):.1f} Hz')

print("\n--- Summary ---")
print("Audio analysis produced spectrogram, dominant-frequency plot, and envelope plot.")
print("See outputs/audio_*.png for visual inspection.")
print("NOTE: Dashcam audio is low-quality mono AAC. Do NOT treat as precise evidence.")
