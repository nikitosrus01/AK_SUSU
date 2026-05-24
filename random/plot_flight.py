import pandas as pd
import matplotlib.pyplot as plt

# ============================================
# LOAD CSV
# ============================================

data = pd.read_csv("flight.csv")

# ============================================
# CONVERT TIME
# ============================================

time = data["TIME_MS"] / 1000.0
altitude = data["ALTITUDE_M"]

# ============================================
# PLOT
# ============================================

plt.figure(figsize=(10, 5))

plt.plot(time, altitude)

plt.xlabel("Time (s)")
plt.ylabel("Altitude (m)")

plt.title("Flight Altitude")

plt.grid(True)

plt.show()