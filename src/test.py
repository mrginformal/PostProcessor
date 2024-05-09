import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom


# Helper function to apply a simple moving average for smoothing
def moving_average(data, window_size):
    """Apply a simple moving average to the data with a specified window size."""
    kernel = np.ones(window_size) / window_size
    return np.convolve(data, kernel, mode='same')


n_values = [50, 60, 55, 65, 100]  # Number of trials
p_values = [0.5, 0.4, .45, .4, .45]  # Probability of success

# Creating a time array
t = np.arange(100)  # A generous range to cover all potential outcomes

# Generate and plot the PMF for each binomial distribution
plt.figure(figsize=(10, 6))
lines = []

for n, p in zip(n_values, p_values):
    # Generating binomial distribution data
    pmf = [binom.pmf(k, n, p) for k in t]
    lines.append(pmf)
    plt.plot(t, pmf, label=f'n={n}, p={p}')

# Stacking all sine waves into a matrix for easier computation
all_waves = np.vstack(lines)

# Calculating the mean and standard deviation along the waves
mean_wave = np.mean(all_waves, axis=0)
std_wave = np.average(all_waves, axis=0)

# Smoothing the mean and standard deviation lines
window_size = 1  # Number of points in the moving average window
smoothed_mean = moving_average(mean_wave, window_size)
smoothed_upper_std = (mean_wave + (2 * std_wave))
smoothed_lower_std = (mean_wave - (2 * std_wave))

# Setup for plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# Plotting the waves and smoothed lines on the first subplot
ax1.plot(t, lines[0], label='Wave 1', alpha=.4)
ax1.plot(t, lines[1], label='Wave 2', alpha=.4)
ax1.plot(t, lines[2], label='Wave 3', alpha=.4)
ax1.plot(t, lines[3], label='Wave 4', alpha=.4)
ax1.plot(t, lines[4], label='Wave 5', alpha=.4)
ax1.plot(t, smoothed_mean, label='Smoothed Mean Wave', color='black', linewidth=2)
ax1.plot(t, smoothed_upper_std, label='Smoothed Mean + 2 Std Dev', linestyle='--', color='red')
ax1.plot(t, smoothed_lower_std, label='Smoothed Mean - 2 Std Dev', linestyle='--', color='blue')

# Filling between the smoothed statistical lines
ax1.fill_between(t, smoothed_lower_std, smoothed_upper_std, color='gray', alpha=0.4)
ax1.set_title('Noisy Sinewaves with Smoothed Statistical Boundaries')
ax1.set_xlabel('Time')
ax1.set_ylabel('Amplitude')
ax1.legend()

# Generating heatmap on the second subplot
heatmap, xedges, yedges = np.histogram2d(np.tile(t, 5), all_waves.ravel(), bins=(50, 30))
extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
ax2.imshow(heatmap.T, extent=extent, origin='lower', aspect='auto', cmap='hot')
ax2.set_title('Heatmap of Sinewave Values')
ax2.set_xlabel('Time')
ax2.set_ylabel('Amplitude')

plt.tight_layout()
plt.show()

