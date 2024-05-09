import numpy as np
import matplotlib.pyplot as plt

# Set the number of waves and parameters for noise and phase deviation
num_waves = 100
phase_deviation = 0.02  # Small phase deviation
noise_level = 0.5       # High noise level

# Time array
t = np.linspace(0, 2 * np.pi, 400)

# Initialize an array to store all wave data
all_waves = np.zeros((num_waves, len(t)))

# Generate each wave with a slight phase shift and add heavy noise
for i in range(num_waves):
    phase_shift = np.random.uniform(-phase_deviation, phase_deviation)
    noise = np.random.normal(0, noise_level, t.shape)
    all_waves[i] = np.sin(t + phase_shift) + noise

# Determine amplitude range and bins for histogram
amplitude_range = (-3, 3)  # Assuming most values fall within this range due to noise
bins = 100  # Number of bins for histogram

# Calculate histogram data for each time point to create heatmap data
heatmap_data = np.zeros((bins, len(t)))
for i in range(len(t)):
    histogram, bin_edges = np.histogram(all_waves[:, i], bins=bins, range=amplitude_range)
    heatmap_data[:, i] = histogram

# Normalize the histogram data by the number of waves to show frequency
heatmap_data = heatmap_data / num_waves

# Plotting the heatmap
plt.figure(figsize=(12, 6))
extent = [t.min(), t.max(), amplitude_range[0], amplitude_range[1]]
plt.imshow(heatmap_data, aspect='auto', extent=extent, origin='lower', cmap='viridis', interpolation='nearest')
plt.colorbar(label='Frequency')
plt.title('Heatmap of 100 Noisy Sine Waves Using Histograms')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.show()


