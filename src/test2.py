import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom

# Parameters for the binomial distributions
n_values = [50, 60, 70, 80, 90]  # Number of trials
p_values = [0.5, 0.4, 0.6, 0.4, 0.5]  # Probability of success

# Creating a time array
t = np.arange(100)  # A generous range to cover all potential outcomes

# Generate and plot the PMF for each binomial distribution
plt.figure(figsize=(10, 6))
for n, p in zip(n_values, p_values):
    # Generating binomial distribution data
    pmf = [binom.pmf(k, n, p) for k in t]
    plt.plot(t, pmf, label=f'n={n}, p={p}')

# Adding labels and legend
plt.title('Binomial Distribution PMFs')
plt.xlabel('Number of Successes (k)')
plt.ylabel('Probability')
plt.legend()
plt.show()
