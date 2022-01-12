import matplotlib.pyplot as plt
import numpy as np

# virus parameters
r = 1.1 # transmission rate
m = 0.03 # mortaility rate

# population parameters
p_init = 10000
rate_inf_0 = 0.1

# variables of the simulation
tmax = 100 # time unit: incubation period of the virus
P_tot = [p_init]
P_inf = [rate_inf_0 * p_init]
P_death = [0]

# simulation
t = 0
while t<tmax-1 and P_tot[-1]>0:
    P_inf.append(int(P_inf[t] * r * (1-m)))
    P_death.append(int(P_death[t] + P_inf[t] * m))
    P_tot.append(P_tot[t] - (P_death[t+1]-P_death[t]))
    t += 1


T = range(t+1)
plt.plot(T, P_inf, label="Infected")
plt.plot(T, P_death, label="Death")
plt.plot(T, P_tot, label="Population")
plt.legend()

plt.show()
