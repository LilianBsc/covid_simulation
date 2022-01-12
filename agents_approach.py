import random
import numpy as np
import matplotlib.pyplot as plt
import time

# ==============================================================================
# PARAMETERS
# ==============================================================================
P_TOT = 5000 # initial population
PAR_RATE = 1/10 # person at risk rate
N_PERS_BY_DAY = 20 # number of different persons enconter by day
N_PERS_BY_DAY_CONF = 3 # number of person encontered by day in containment
INFECTED_RATE = 0.015 # initial infected rate
R0 = 1.1 # r0 of the virus
PERSISTENCE = 15 # persistance of the virus
PERSISTENCE_ANTICORPS = 30*3 # duration of the anticorps 6 months
M_PAR = 0.03 # person at risk mortaility rate (10 times more than non par)
M_NON_PAR = 0.03/13 # non person at risk mortaility rate (mortality rate total = 0.005)

RATE_OF_PERMANENT_EXCHANGES = 0.003 # rate of exchanges at the borders
RATE_OF_TEMPORARY_EXCHANGES = 0.05 # rate of exchanges for a period betwin 1-7 days
INITIAL_VACCINATION_RATE = 0.002 # rate of vaccination by day
VACCIN_EFFICACY = 0.94 # rate of efficacy of the vaccin
PCR_ACCURACY = 0.70 # accuracy of the PCR test
VACCINAL_PASS_AT_BOARDER = False # vaccinal pass at the boarders
PCR_PASS_AT_BOARDER = True # PCR test at the boarders

DURATION_OF_SIMULATION = 2*365 # duration of the simulation
N_DAYS_BEFORE_VACCIN = 0

TEMPERATURE_SEASONS = [0.2, 1, 3.7, 5.3, 9, 12.8, 15.1, 14.7, 11, 8, 4.7, 3.1,
                       0.2, 1, 3.7, 5.3, 9, 12.8, 15.1, 14.7, 11, 8, 4.7, 3.1,
                       0.2, 1, 3.7, 5.3, 9, 12.8, 15.1, 14.7, 11, 8, 4.7, 3.1,
                       ]
MONTHS_CONTAINMENT = [4, 5, 6, 11, 12, 15, 16, 17] # numero of the months of containment
# ==============================================================================


class Agent:
    def __init__(self, ID):
        self.ID = ID
        if random.random() < PAR_RATE:
            self.risky_person = True
        else:
            self.risky_person = False
        self.is_infected = False
        self.infected_since = None
        self.is_vaccinated = False
        self.immune = False
        self.immune_since = None
        self.p_social_perso = random.random()
        self.is_tourist = False
        self.stay_time = None
        self.here_since = None

    def __repr__(self):
        return f"agent {self.ID}"


def create_pop(N, initial_rate):
    P_tot = []
    for k in range(N):
        P_tot.append(Agent(k+1))
    for agent in P_tot:
        if random.random() < initial_rate:
            agent.is_infected = True
            agent.infected_since = 0
    return P_tot

mu = 3
sigma = 0.9
def calculate_r_virus(r0):
    S = 0
    for t in range(8):
        S += np.exp(-(t-mu)**2/2/sigma**2)
    return  r0/S/N_PERS_BY_DAY

def proba_contagion(t, r):
    return r*np.exp(-(t-mu)**2/(2*sigma**2))

def count_infected(P_tot):
    c = 0
    for agent in P_tot:
        if agent.is_infected:
            c += 1
    return c

def count_immune(P_tot):
    c = 0
    for agent in P_tot:
        if agent.immune:
            c += 1
    return c

def count_risky(P_tot):
    c = 0
    for agent in P_tot:
        if agent.risky_person:
            c += 1
    return c

def count_vaccinated(P_tot):
    c = 0
    for agent in P_tot:
        if agent.is_vaccinated:
            c += 1
    return c

def open_borders(P_tot, rate_permanent_exchanges, vaccin_pass=False, pcr_pass=False):
    # Permanenent exchanges
    outers = [random.choice(P_tot) for _ in range(int(2 * len(P_tot) * rate_permanent_exchanges * random.random()))]
    c_outers = 0
    for outer in outers:
        if outer in P_tot:
            P_tot.remove(outer)
            c_outers += 1
    if pcr_pass:
        inners = create_pop(c_outers, (1 - PCR_ACCURACY) * INFECTED_RATE)
    else:
        inners = create_pop(c_outers, INFECTED_RATE)

    if vaccin_pass:
        for inner in inners:
            inner.is_vaccinated = True
            if random.random() < VACCIN_EFFICACY:
                inner.immune = True
                inner.immune_since = 0
            else:
                inner.immune = False
    P_tot += inners


def create_temporary_exchanges_boarders(P_tot, rate_temporary_exchanges, vaccin_pass=False, pcr_pass=False):
    # Temporary entrance
    if pcr_pass:
        tourists = create_pop(int(2 * len(P_tot) * rate_temporary_exchanges), (1 - PCR_ACCURACY) * INFECTED_RATE)
    else:
        tourists = create_pop(int(2 * len(P_tot) * rate_temporary_exchanges), INFECTED_RATE)

    for tourist in tourists:
        tourist.is_tourist = True
        tourist.stay_time = random.randint(1, 8)
        tourist.here_since = 0

    if vaccin_pass:
        for tourist in tourists:
            tourist.is_vaccinated = True
            if random.random() < VACCIN_EFFICACY:
                tourist.immune = True
            else:
                tourist.immune = False
    return tourists

def manage_temporary_exchanges_boaders(P_tot, tourists, r_virus, containment=False, vaccin_pass=False, pcr_pass=False):
    for tourist in tourists:
        # flux
        tourist.here_since += 1
        if tourist.here_since >= tourist.stay_time:
            tourists.remove(tourist)
            new_tourist = Agent(0)
            new_tourist.is_tourist = True
            new_tourist.stay_time = random.randint(1, 8)
            new_tourist.here_since = 0
            if pcr_pass:
                if random.random() < (1 - PCR_ACCURACY) * INFECTED_RATE:
                    new_tourist.is_infected = True
                    new_tourist.infected_since = 0
            else:
                if random.random() < INFECTED_RATE:
                    new_tourist.is_infected = True
                    new_tourist.infected_since = 0
            if vaccin_pass:
                new_tourist.is_vaccinated = True
                if random.random() < VACCIN_EFFICACY:
                    new_tourist.immune = True
                else:
                    new_tourist.immune = False
            tourists.append(new_tourist)

        # contamination
        if containment:
            contacts = [random.choice(P_tot) for _ in range(int(N_PERS_BY_DAY_CONF*tourist.p_social_perso))]
        else:
            contacts = [random.choice(P_tot) for _ in range(int(N_PERS_BY_DAY*tourist.p_social_perso))]
        if tourist.is_infected:
            tourist.infected_since += 1
            for contact in contacts:
                if not contact.is_infected:
                    if random.random() < proba_contagion(tourist.infected_since, r_virus):
                        contact.is_infected = True
                        contact.infected_since = 0
        elif not tourist.immune:
            # contagion
            for contact in contacts:
                if contact.is_infected:
                    if random.random() < proba_contagion(contact.infected_since, r_virus):
                        tourist.is_infected = True
                        tourist.infected_since = 0
    print(len(tourists))


def vaccination(P_tot, vaccination_rate):
    non_infected = []
    for agent in P_tot:
        if not agent.is_infected and not agent.is_vaccinated:
            non_infected.append(agent)
    if non_infected == []:
        print("End of the epidemy.")
        return True
    vaccinated = [random.choice(P_tot) for _ in range(int(vaccination_rate * len(P_tot) * random.random() * 2))]
    for agent in vaccinated:
        agent.is_vaccinated = True
        if random.random() < VACCIN_EFFICACY:
            agent.immune = True
            agent.immune_since = 0
        else:
            agent.immune = False
    return False

def calculate_vaccination_rate(vaccination_rate, jour):
    return vaccination_rate * jour/100

def modify_r_virus_season(jour, r_virus):
    # add seasons contamination rate 1% each degree
    mois = jour//31
    temp = TEMPERATURE_SEASONS[mois]
    mean_temp = sum(TEMPERATURE_SEASONS)/12
    d = temp - mean_temp
    coeff = 1 - d/100
    return r_virus*coeff

def next_step(P_tot, r_virus, persistence, containment=False):
    dead = []
    for agent in P_tot:
        if containment:
            contacts = [random.choice(P_tot) for _ in range(int(N_PERS_BY_DAY_CONF*agent.p_social_perso))]
        else:
            contacts = [random.choice(P_tot) for _ in range(int(N_PERS_BY_DAY*agent.p_social_perso))]
        for contact in contacts:
            if contact.immune:
                contacts.remove(contact)

        if agent.is_infected:
            if agent.infected_since < 7:
                agent.infected_since += 1
                # contagion
                for contact in contacts:
                    if not contact.is_infected:
                        if random.random() < proba_contagion(agent.infected_since, r_virus):
                            contact.is_infected = True
                            contact.infected_since = 0
                # death
                if agent.risky_person :
                    p_death = M_PAR
                    if random.random() < p_death:
                        P_tot.remove(agent)
                        dead.append(agent)
                else:
                    p_death = M_NON_PAR
                    if random.random() < p_death:
                        P_tot.remove(agent)
                        dead.append(agent)

            # self healing
            else:
                agent.is_infected = False
                agent.infected_since = None
                agent.immune = True
                agent.immune_since = 0


        elif not agent.immune:
            # contagion
            for contact in contacts:
                if contact.is_infected:
                    if random.random() < proba_contagion(contact.infected_since, r_virus):
                        agent.is_infected = True
                        agent.infected_since = 0
        elif agent.immune:
            agent.immune_since += 1
            if agent.immune_since > PERSISTENCE_ANTICORPS:
                agent.immune = False
                agent.immune_since = None
                agent.is_vaccinated = False
    return dead

def simulation(n_pop, initial_rate, r_virus, persistence, n_jours):
    P_tot = create_pop(n_pop, initial_rate)
    tourists = create_temporary_exchanges_boarders(P_tot, RATE_OF_TEMPORARY_EXCHANGES, vaccin_pass=VACCINAL_PASS_AT_BOARDER, pcr_pass=PCR_PASS_AT_BOARDER)
    n_inf = [count_infected(P_tot)]
    n_tot = [n_pop]
    n_death = [0]
    n_immune = [0]
    n_vaccinated = [0]
    agents_dead = []
    plt.ion()
    # figure, axis = plt.subplots(1, 2)
    end_of_epidemy = False
    for jour in range(n_jours):
        open_borders(P_tot, RATE_OF_PERMANENT_EXCHANGES, vaccin_pass=VACCINAL_PASS_AT_BOARDER, pcr_pass=PCR_PASS_AT_BOARDER)
        if jour > N_DAYS_BEFORE_VACCIN:
            vaccination_rate = calculate_vaccination_rate(INITIAL_VACCINATION_RATE, jour)
            end_of_epidemy = vaccination(P_tot, vaccination_rate)
        if end_of_epidemy:
            n_jours = jour
            break
        r_virus_modify = modify_r_virus_season(jour, r_virus)
        if jour//31+1 in MONTHS_CONTAINMENT:
            dead = next_step(P_tot, r_virus_modify, persistence, containment=True)
            manage_temporary_exchanges_boaders(P_tot, tourists, r_virus, containment=True, vaccin_pass=VACCINAL_PASS_AT_BOARDER, pcr_pass=PCR_PASS_AT_BOARDER)
        else:
            dead = next_step(P_tot, r_virus_modify, persistence)
            manage_temporary_exchanges_boaders(P_tot, tourists, r_virus, containment=False, vaccin_pass=VACCINAL_PASS_AT_BOARDER, pcr_pass=PCR_PASS_AT_BOARDER)
        # dead = next_step(P_tot, r_virus, persistence)
        agents_dead += dead
        n_inf.append(count_infected(P_tot))
        n_tot.append(len(P_tot))
        n_death.append(len(agents_dead))
        n_immune.append(count_immune(P_tot))
        n_vaccinated.append(count_vaccinated(P_tot))
        print(f"day {jour}:\ndeath={n_death[-1]}, infected={n_inf[-1]}, immune={n_immune[-1]}, vaccinated={n_vaccinated[-1]}, contamination rate={round(r_virus_modify, 4)}, total population={n_tot[-1]}")
        # print(f"day {jour}:\ndeath={n_death[-1]}, infected={n_inf[-1]}, immune={n_immune[-1]}, vaccinated={n_vaccinated[-1]}, total population={n_tot[-1]}")
        T = range(jour+2)
        plt.plot(T, n_inf, label="Infected")
        plt.plot(T, n_death, label="Death")
        plt.plot(T, n_immune, label="Immune")
        plt.plot(T, n_vaccinated, label="Vaccinated")
        plt.legend()
        # axis[1].plot(T, n_tot, label="Population")
        # axis[1].legend()
        plt.draw()
        plt.pause(0.0001)
        plt.clf()

    print(f"death={len(agents_dead)}, person at risk={round(count_risky(agents_dead)*100/max(len(agents_dead),0.1), 2)}%")
    # plt.show()
    return n_death, n_inf, n_immune, n_vaccinated, n_tot, n_jours

def show(history):
    plt.ioff()
    n_death, n_inf, n_immune, n_vaccinated, n_tot, n_jours = history[0], history[1], history[2], history[3], history[4], history[5]
    T = range(n_jours+1)
    figure, axis = plt.subplots(2, 2)
    axis[0, 0].plot(T, n_inf, label="Infected")
    axis[0, 1].plot(T, n_death, label="Death")
    axis[1, 0].plot(T, n_immune, label="Immune")
    axis[1, 0].plot(T, n_vaccinated, label="Vaccinated")
    axis[0, 0].legend()
    axis[1, 0].legend()
    axis[0, 1].legend()
    axis[1, 1].plot(T, n_tot, label="Population")
    axis[1, 1].legend()
    plt.show()

r_virus = calculate_r_virus(R0)

history = simulation(P_TOT, INFECTED_RATE, r_virus, PERSISTENCE, DURATION_OF_SIMULATION)
show(history)
