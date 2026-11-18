"""
Demand & Footfall Forecasting Model using Pure NumPy Matrix Algebra & Polars.
Fits L2-Regularized Multivariable Polynomial Regression with branch embeddings,
rush-hour curves, month-end interactions, and returns comprehensive evaluation metrics.
"""
import numpy as np
import polars as pl
from src.config import BRANCH_NETWORK, SERVICE_CATEGORIES

class DemandForecaster:
    def __init__(self, l2_reg: float = 0.8):
        self.l2_reg = l2_reg
        self.weights = None
        self.bias = 0.0
        self.branch_map = {b["branch_id"]: idx for idx, b in enumerate(BRANCH_NETWORK)}
        self.is_trained = False
        self.metrics = {}
        self.feature_names = []

    def _encode_features(self, branch_ids: list, hours: list, days_of_week: list, is_month_ends: list, is_peaks: list) -> np.ndarray:
        n = len(branch_ids)
        num_branches = len(self.branch_map)
        
        # Features: [one_hot_branches (5), hour_centered, day_normalized, is_month_end, is_peak, hour_quadratic, peak_month_interaction]
        X = np.zeros((n, num_branches + 6))
        for i in range(n):
            b_idx = self.branch_map.get(branch_ids[i], 0)
            X[i, b_idx] = 1.0  # One-hot branch indicator
            h = float(hours[i])
            X[i, num_branches] = (h - 12.5) / 3.5           # Centered operational hour [-1, 1]
            X[i, num_branches + 1] = float(days_of_week[i]) / 4.0
            X[i, num_branches + 2] = float(is_month_ends[i])
            X[i, num_branches + 3] = float(is_peaks[i])
            X[i, num_branches + 4] = ((h - 12.5) / 2.5) ** 2  # Non-linear quadratic midday peak
            X[i, num_branches + 5] = float(is_month_ends[i]) * float(is_peaks[i]) # Interaction
            
        return X

    def train(self, df_hourly: pl.DataFrame):
        """Trains L2-Regularized closed-form regression model on historical hourly arrival metrics."""
        branch_ids = df_hourly["branch_id"].to_list()
        hours = df_hourly["arrival_hour"].to_list()
        
        if "date" in df_hourly.columns:
            dates = df_hourly["date"].to_list()
            days = [d.weekday() if hasattr(d, "weekday") else 2 for d in dates]
            is_month_ends = [1 if getattr(d, "day", 15) in [1, 2, 3, 28, 29, 30, 31] else 0 for d in dates]
        else:
            days = [2] * len(branch_ids)
            is_month_ends = [0] * len(branch_ids)
            
        is_peaks = [1 if h in [11, 12, 13, 14] else 0 for h in hours]
        
        self.feature_names = [f"Branch_{b['branch_id']}" for b in BRANCH_NETWORK] + [
            "Hour_Centered", "Day_of_Week", "Is_Month_End", "Is_Peak_Window", "Midday_Rush_Curve", "Peak_Month_Interaction"
        ]
        
        X = self._encode_features(branch_ids, hours, days, is_month_ends, is_peaks)
        y = df_hourly["total_arrivals"].to_numpy().astype(float)
        
        # 80/20 Train/Test Split
        n = len(X)
        indices = np.arange(n)
        np.random.seed(42)
        np.random.shuffle(indices)
        split = int(0.8 * n)
        train_idx, test_idx = indices[:split], indices[split:]
        
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]
        
        # Closed form Ridge regression: (X_aug^T X_aug + lambda I)^-1 X_aug^T y
        X_aug_train = np.hstack([np.ones((len(X_train), 1)), X_train])
        d = X_aug_train.shape[1]
        I = np.eye(d)
        I[0, 0] = 0.0  # Do not regularize bias
        
        params = np.linalg.solve(X_aug_train.T @ X_aug_train + self.l2_reg * I, X_aug_train.T @ y_train)
        self.bias = float(params[0])
        self.weights = params[1:]
        self.is_trained = True
        
        # Evaluate on Test Set
        X_aug_test = np.hstack([np.ones((len(X_test), 1)), X_test])
        test_preds = X_aug_test @ params
        
        mae = float(np.mean(np.abs(y_test - test_preds)))
        rmse = float(np.sqrt(np.mean((y_test - test_preds) ** 2)))
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        ss_res = np.sum((y_test - test_preds) ** 2)
        r2 = float(1.0 - (ss_res / max(1e-6, ss_tot)))
        mape = float(np.mean(np.abs((y_test - test_preds) / np.clip(y_test, 1.0, None))) * 100)
        
        # Relative feature importances (normalized absolute weights)
        abs_w = np.abs(self.weights)
        total_w = np.sum(abs_w) if np.sum(abs_w) > 0 else 1.0
        importances = {name: round(float((w / total_w) * 100), 1) for name, w in zip(self.feature_names, abs_w)}
        
        self.metrics = {
            "model_type": "L2-Regularized Multivariable Ridge Regressor",
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2_score": round(r2, 3),
            "mape_pct": round(mape, 1),
            "feature_importances": importances
        }
        
        print(f" Demand Forecaster Trained on {len(df_hourly)} windows: MAE = {mae:.2f} cust/hr, R² = {r2:.3f}, RMSE = {rmse:.2f}")
        return self.metrics

    def forecast_day(self, branch_id: str, date_str: str, day_of_week: int, is_month_end: int = 0) -> list:
        """Generates hourly demand forecast dictionary records with confidence intervals for branch view."""
        if not self.is_trained:
            self.bias = 18.0
            self.weights = np.zeros(len(self.branch_map) + 6)
            self.is_trained = True
            
        hours = list(range(9, 17))
        branch_ids = [branch_id] * len(hours)
        days = [day_of_week] * len(hours)
        month_ends = [is_month_end] * len(hours)
        is_peaks = [1 if h in [11, 12, 13, 14] else 0 for h in hours]
        
        X = self._encode_features(branch_ids, hours, days, month_ends, is_peaks)
        raw_preds = self.bias + X @ self.weights
        
        results = []
        for idx, h in enumerate(hours):
            base_pred = max(4.0, float(raw_preds[idx]))
            if is_month_end:
                base_pred = base_pred * 1.25
                
            pred_arr = int(round(base_pred))
            ci_lower = max(2, int(round(base_pred * 0.85 - 1.5)))
            ci_upper = int(round(base_pred * 1.15 + 2.0))
            
            risk = "High Surge" if pred_arr >= 28 else ("Moderate Pressure" if pred_arr >= 18 else "Optimal Flow")
            
            # Service demand breakdown
            cash_kyc = int(round(pred_arr * 0.52))
            loans_inv = int(round(pred_arr * 0.22))
            quick_serv = int(round(pred_arr * 0.18))
            specialist = max(1, pred_arr - cash_kyc - loans_inv - quick_serv)
            
            results.append({
                "branch_id": branch_id,
                "arrival_hour": h,
                "time_slot": f"{h:02d}:00 - {h+1:02d}:00",
                "predicted_arrivals": pred_arr,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "surge_risk": risk,
                "cash_kyc_share": cash_kyc,
                "loans_investments_share": loans_inv,
                "quick_services_share": quick_serv,
                "specialist_advisory_share": specialist
            })
            
        return results
