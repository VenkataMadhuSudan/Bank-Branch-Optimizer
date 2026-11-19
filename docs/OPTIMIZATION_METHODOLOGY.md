# MATHEMATICAL STAFF OPTIMIZATION & BREAK SCHEDULING METHODOLOGY

**Engine:** Google OR-Tools CP-SAT (Constraint Programming - Satisfiability)  
**Problem Class:** Multi-Skill Worker-to-Task Assignment with Staggered Window Constraint Programming  
**Module:** `src/optimization/staff_optimizer.py`  
**Reference Benchmark:** `VitalOptima/models/optimizer.py`  

---

## 1. Problem Definition & Mathematical Formulation

In retail banking networks, customer arrival rates vary non-linearly throughout the business day, peaking during lunch hours (11:30–14:00) and month-end cycles. Teller and specialist desks must be dynamically allocated to eradicate queue bottlenecks while respecting employee primary/secondary skill certifications, physical counter limits, and mandatory labor break requirements.

### 1.1 Index Sets & Parameters
- $\mathcal{I} = \{1, \dots, N\}$: Set of available active employees.
- $\mathcal{C} = \{1, \dots, K\}$: Set of physical operational counters ($K \le \text{AvailableCounters}$).
- $\mathcal{S}$: Set of service categories (Cash, KYC, Loans, Forex, Passbook, Cards, Wealth).
- $\mathcal{T} = \{1, \dots, M\}$: Set of staggered lunch break windows (e.g. 11:30–12:15, 12:15–13:00, 13:00–13:45, 13:45–14:30).
- $D_s \ge 0$: Hourly customer arrival demand for service $s \in \mathcal{S}$.
- $W_s \ge 0$: Acuity priority penalty for unmet demand in service $s$.
- $\text{Speed}_i \in [1.0, 5.0]$: Historical transaction speed rating of employee $i$.
- $\text{Primary}_i \in \mathcal{S}$: Primary certified specialty of employee $i$.
- $\text{Secondary}_i \subseteq \mathcal{S}$: Certified secondary flex competencies.

### 1.2 Decision Variables
- $x_{i, c, s} \in \{0, 1\}$: Binary variable equal to $1$ if employee $i \in \mathcal{I}$ is assigned to Counter $c \in \mathcal{C}$ serving Service $s \in \mathcal{S}$.
- $y_i \in \{0, 1\}$: Binary indicator equal to $1$ if employee $i$ is actively assigned to any counter.
- $b_{i, t} \in \{0, 1\}$: Binary indicator equal to $1$ if employee $i$ takes their mandatory meal break during time window $t \in \mathcal{T}$.

---

## 2. Hard Physical & Operational Constraints

1. **Staff Exclusivity (No Simultaneous Counters):**
   An employee can occupy at most one counter and serve at most one service:
   $$\sum_{c \in \mathcal{C}} \sum_{s \in \mathcal{S}} x_{i, c, s} = y_i \le 1, \quad \forall i \in \mathcal{I}$$

2. **Counter Exclusivity (At Most One Teller per Desk):**
   A physical counter can host at most one staff member:
   $$\sum_{i \in \mathcal{I}} \sum_{s \in \mathcal{S}} x_{i, c, s} \le 1, \quad \forall c \in \mathcal{C}$$

3. **Mandatory Break Conservation:**
   Every active working employee must be assigned exactly one break slot; unassigned buffer staff take non-operational breaks:
   $$\sum_{t \in \mathcal{T}} b_{i, t} = y_i, \quad \forall i \in \mathcal{I}$$

4. **Anti-Starvation Staggered Break Bound:**
   To prevent counter starvation during high-demand windows, the number of staff simultaneously on break in window $t$ is bounded by:
   $$\sum_{i \in \mathcal{I}} b_{i, t} \le \left\lfloor \frac{|\mathcal{C}|}{|\mathcal{T}|} \right\rfloor + 1, \quad \forall t \in \mathcal{T}$$

---

## 3. Objective Function Formulation

The solver maximizes a weighted sum of demand satisfaction, skill-to-task compatibility, and counter speed efficiency:

$$\max \sum_{i \in \mathcal{I}} \sum_{c \in \mathcal{C}} \sum_{s \in \mathcal{S}} x_{i, c, s} \cdot \Big[ \text{SkillMatchScore}(i, s) + \text{SpeedBonus}(i) + \text{ServicePriority}(s) \Big]$$

Where:
$$\text{SkillMatchScore}(i, s) = \begin{cases} 
100, & \text{if } s = \text{Primary}_i \\ 
70, & \text{if } s \in \text{Secondary}_i \\ 
30, & \text{otherwise (Dynamic Surge Relief)} 
\end{cases}$$

$$\text{SpeedBonus}(i) = \lfloor 10 \cdot \text{Speed}_i \rfloor$$

---

## 4. Solver Reliability & Infeasibility Handling

1. **Solver Time Limits:** Configured with a default cutoff of 5.0 seconds.
2. **Status Reporting:** Returns explicit mathematical status:
   - `OPTIMAL`: Globally proven optimal allocation under constraints.
   - `FEASIBLE`: Valid constraint-compliant solution found within time limit.
   - `INFEASIBLE`: Problem mathematically cannot be satisfied under current constraints.
   - `HEURISTIC_FALLBACK`: Clearly labeled fallback invoked when solver is unavailable or fails. Never falsely claims mathematical optimality.
3. **Independent Solution Validator:** An independent verification pass verifies that:
   - No employee ID appears twice in the assignment.
   - No counter ID is shared.
   - All assigned skills match employee profiles.
   - Every working employee has an assigned break slot.
