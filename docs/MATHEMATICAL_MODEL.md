# MATHEMATICAL FOUNDATIONS & ALGORITHMIC FORMULATIONS

**Project:** Bank AI Optimizer  
**Core Fields:** Operations Research, Constraint Programming, Discrete-Event Stochastic Simulation, Conformal Inference  

---

## 1. Mixed-Integer Linear Constraint Programming (Staff Optimization)

### Indices & Sets
- $i \in \mathcal{I} = \{1, \dots, N\}$: Available bank employees.
- $c \in \mathcal{C} = \{1, \dots, K\}$: Physical service counters ($K \le \text{AvailableCounters}$).
- $s \in \mathcal{S}$: Service transaction categories (Cash, KYC, Loan, Forex, Passbook, Card, Wealth).
- $t \in \mathcal{T} = \{1, \dots, M\}$: Staggered lunch break slots (11:30–12:15, 12:15–13:00, 13:00–13:45, 13:45–14:30).

### Decision Variables
- $x_{i, c, s} \in \{0, 1\}$: $1$ if employee $i$ is assigned to counter $c$ handling service $s$.
- $y_i \in \{0, 1\}$: $1$ if employee $i$ is actively assigned to any counter.
- $b_{i, t} \in \{0, 1\}$: $1$ if employee $i$ takes their mandatory break during slot $t$.

### Exact Formulation
$$\max \sum_{i \in \mathcal{I}} \sum_{c \in \mathcal{C}} \sum_{s \in \mathcal{S}} x_{i, c, s} \Big[ \text{SkillScore}(i, s) + \text{SpeedBonus}(i) + \text{Priority}(s) \Big]$$

$$\text{s.t.} \quad \sum_{c \in \mathcal{C}} \sum_{s \in \mathcal{S}} x_{i, c, s} = y_i \le 1, \quad \forall i \in \mathcal{I}$$
$$\sum_{i \in \mathcal{I}} \sum_{s \in \mathcal{S}} x_{i, c, s} \le 1, \quad \forall c \in \mathcal{C}$$
$$\sum_{t \in \mathcal{T}} b_{i, t} = y_i, \quad \forall i \in \mathcal{I}$$
$$\sum_{i \in \mathcal{I}} b_{i, t} \le \left\lfloor \frac{|\mathcal{C}|}{|\mathcal{T}|} \right\rfloor + 1, \quad \forall t \in \mathcal{T}$$

---

## 2. Two-Stage Stochastic Programming under Arrival Uncertainty

### Stage 1 (Here-and-Now Decisions)
- $N_c \in \{0, 1\}$: Baseline operational counter staffed before shift realization.
- Cost: $C_{\text{base}} = \$28.00/\text{hr}$.

### Stage 2 (Recourse Decisions under Scenario $s \in \mathcal{S}$ with Probability $p_s$)
- $v_{s, c} \in \{0, 1\}$: Flex overtime / temporary counter activation ($C_{\text{flex}} = \$45.00/\text{hr}$).
- $u_{s, k} \ge 0$: Unmet customer demand for service $k$ under scenario $s$.

$$\min \sum_{c} C_{\text{base}} N_c + \sum_{s \in \mathcal{S}} p_s \left[ \sum_c C_{\text{flex}} v_{s, c} + \sum_k W_k u_{s, k} \right]$$
$$\text{s.t.} \quad N_c + v_{s, c} \le 1, \quad \forall c, s$$
$$\sum_c (N_c + v_{s, c}) \cdot \text{Capacity} + \sum_k u_{s, k} \ge \text{TotalDemand}_s, \quad \forall s$$

---

## 3. Split Conformal Prediction Intervals

Given non-conforming residuals on untouched calibration set:
$$R_i = |y_i - \hat{y}(x_i)|, \quad i \in \mathcal{D}_{\text{calib}}$$
The finite-sample corrected quantile at significance $\alpha = 0.10$ (90% coverage) is:
$$\hat{q} = \text{Quantile}\left( \{R_i\}, \frac{\lceil (n+1)(1-\alpha) \rceil}{n} \right)$$
Generating distribution-free prediction bounds:
$$C(x) = [\hat{y}(x) - \hat{q}, \quad \hat{y}(x) + \hat{q}]$$
Guaranteeing $\mathbb{P}(y \in C(x)) \ge 1 - \alpha$.
