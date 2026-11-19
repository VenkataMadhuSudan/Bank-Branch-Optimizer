# DEMAND FORECASTING METHODOLOGY & BENCHMARKING

**Module:** `src/models/demand_forecaster.py`  
**Reference Benchmark:** `VitalOptima/models/forecaster.py`  

---

## 1. Zero Data Leakage Time-Series Validation

In earlier iterations of Bank AI Optimizer, random shuffling (`np.random.shuffle`) was used for cross-validation. In time-series forecasting, this introduces severe temporal data leakage by allowing the model to train on future observations to predict past points.

### Chronological 80/20 Split
All historical observations are ordered chronologically by `[date, arrival_hour]`:
$$\mathcal{D}_{\text{train}} = \{ (x_t, y_t) \}_{t=1}^{T_{\text{split}}}, \quad \mathcal{D}_{\text{test}} = \{ (x_t, y_t) \}_{t=T_{\text{split}}+1}^{T}$$
Where $T_{\text{split}} = \lfloor 0.80 \cdot T \rfloor$. The test set remains strictly out-of-sample and untouched during feature scaling and parameter tuning.

---

## 2. Model Benchmark Suite

Four candidate architectures are trained and compared under identical chronological splits:

1. **Seasonal Naive Baseline:** Projects the historical average of the identical branch and operational hour from the training set.
2. **L2-Regularized Ridge Regression:** Multivariable linear regression with penalty $\lambda = 1.0$, preventing collinear feature overfitting.
3. **Random Forest Regressor:** Non-linear decision tree ensemble ($N=50, \text{max\_depth}=6$) capturing complex diurnal midday interactions.
4. **HistGradientBoosting Regressor:** Fast binned gradient boosting capturing non-linear threshold effects.

---

## 3. Evaluation Metrics Matrix

The models are evaluated on the out-of-sample test split using standard regression metrics:
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$
- **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}$$
- **Weighted Absolute Percentage Error (WAPE):**
  $$\text{WAPE} = \frac{\sum_{i=1}^n |y_i - \hat{y}_i|}{\sum_{i=1}^n y_i} \times 100\%$$
- **Coefficient of Determination ($R^2$):**
  $$R^2 = 1 - \frac{\sum_{i=1}^n (y_i - \hat{y}_i)^2}{\sum_{i=1}^n (y_i - \bar{y})^2}$$

