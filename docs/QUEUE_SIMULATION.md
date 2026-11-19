# QUEUE SIMULATION & STOCHASTIC CAPACITY PLANNING

**Module:** `src/optimization/queue_simulator.py`, `src/optimization/stochastic_optimizer.py`  
**Simulation Engine:** Discrete-Event Monte Carlo with Independent Random Number Generators (`numpy.random.default_rng`)  
**Analytical Model:** Erlang-C ($M/M/c$) Delay Probability Benchmark  
**Stochastic Model:** Two-Stage Recourse Stochastic Optimization (Google OR-Tools CP-SAT)  

---

## 1. Discrete-Event Simulation Architecture

The queue simulation engine models dynamic customer arrivals, counter processing, priority scheduling, and customer abandonment over a multi-hour business shift.

### 1.1 Non-Homogeneous Poisson Arrival Process
Customer arrivals follow an exponential inter-arrival distribution parameterized by time-varying arrival rate $\lambda(t)$:
$$\tau_{k+1} = \tau_k + \Delta t_k, \quad \Delta t_k \sim \text{Exponential}\left(\frac{1}{\lambda(t)}\right)$$
Where $\lambda(t)$ incorporates peak midday curves, month-end multipliers, and digital deflection discounts:
$$\lambda_{\text{effective}}(t) = \lambda_{\text{base}}(t) \cdot \left(1 - \frac{\text{DeflectionRate}}{100}\right)$$

### 1.2 Lognormal Service Time Distribution
Empirical banking teller durations exhibit positive skewness. The engine models service time $S$ using a lognormal distribution:
$$\ln(S) \sim \mathcal{N}\left(\mu_{\ln}, \sigma_{\ln}^2\right)$$
Where:
$$\sigma_{\ln} = 0.35, \quad \mu_{\ln} = \ln(\mu_{\text{service}}) - \frac{\sigma_{\ln}^2}{2}$$
Ensuring $\mathbb{E}[S] = \mu_{\text{service}}$ while eliminating unrealistic negative service times.

### 1.3 Multi-Class Customer Priority & Reneging (Abandonment)
Incoming clients are mapped to 4 customer segments with empirical patience thresholds $T_{\text{patience}} \sim \mathcal{N}(\mu_{\text{pat}}, \sigma_{\text{pat}})$:
- **High Net Worth (HNI/VIP):** Mean patience 12.0 mins ($\sigma = 3.0$).
- **Senior Citizen:** Mean patience 20.0 mins ($\sigma = 4.0$).
- **Small Business / SME:** Mean patience 18.0 mins ($\sigma = 4.0$).
- **Regular Individuals:** Mean patience 25.0 mins ($\sigma = 5.0$).

If a customer's waiting time exceeds their patience threshold ($W_i > T_{\text{patience}, i}$), the customer **reneges (abandons)** the queue.

---

## 2. Erlang-C ($M/M/c$) Theoretical Comparison

For situations where Markovian assumptions hold ($\rho < 1.0$), the simulator benchmarks empirical wait times against the analytical Erlang-C queueing formula:

$$\rho = \frac{\lambda}{c \mu}, \quad a = \frac{\lambda}{\mu}$$

$$P_c = \frac{\frac{a^c}{c!(1-\rho)}}{\sum_{k=0}^{c-1} \frac{a^k}{k!} + \frac{a^c}{c!(1-\rho)}}$$

$$W_q = \frac{P_c}{c\mu - \lambda} \times 60 \quad (\text{minutes})$$

This provides an exact theoretical comparison to validate whether the discrete-event simulation converges to analytical queueing theory.

---

## 3. Two-Stage Stochastic Capacity Planning

To handle uncertain demand, the engine formulates a Two-Stage Stochastic Program:

### Stage 1 (Here-and-Now Decisions)
- $N_c \in \{0, 1\}$: Base regular counters committed prior to shift start.
- Fixed operational cost: $C_{\text{base}} = \$28.00/\text{hour}$.

### Stage 2 (Wait-and-See Recourse Decisions)
- Scenarios $s \in \{\text{P10 Low, P50 Median, P90 High, Month-End Surge}\}$ with probabilities $p_s$.
- $v_{s, c} \in \{0, 1\}$: Flex overtime / temporary counter activation ($C_{\text{flex}} = \$45.00/\text{hour}$).
- $u_{s, k} \ge 0$: Unmet customer demand penalized by service priority $W_k$.

### Objective
$$\min \sum_{c} C_{\text{base}} N_c + \sum_{s \in \mathcal{S}} p_s \left[ \sum_c C_{\text{flex}} v_{s, c} + \sum_k W_k u_{s, k} \right]$$

This balances base labor expenditure against recourse overtime costs under demand variance.

