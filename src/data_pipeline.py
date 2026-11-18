"""
Data Preprocessing, Feature Engineering, and Queue Metrics Ingestion Pipeline using Polars and Python stdlib.
"""
import polars as pl
import numpy as np
import csv
from pathlib import Path
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SERVICE_CATEGORIES

class BankingDataPipeline:
    def __init__(self, raw_dir: Path = RAW_DATA_DIR, processed_dir: Path = PROCESSED_DATA_DIR):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

    def load_raw_data(self):
        """Loads all raw CSV files into Polars DataFrames."""
        tokens = pl.read_csv(self.raw_dir / "branch_queue_logs.csv")
        staff = pl.read_csv(self.raw_dir / "staff_rosters.csv")
        branches = pl.read_csv(self.raw_dir / "branch_metadata.csv")
        feedback = pl.read_csv(self.raw_dir / "customer_feedback.csv")
        appointments = pl.read_csv(self.raw_dir / "appointments.csv")
        return tokens, staff, branches, feedback, appointments

    def preprocess_tokens(self, df_tokens: pl.DataFrame) -> pl.DataFrame:
        """Cleans timestamps, extracts hour/calendar features, and validates queue durations."""
        df = df_tokens.with_columns([
            pl.col("arrival_timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("arrival_dt"),
            pl.col("service_start_timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("service_start_dt"),
            pl.col("service_end_timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("service_end_dt"),
        ])
        
        df = df.with_columns([
            pl.col("arrival_dt").dt.hour().alias("arrival_hour"),
            pl.col("arrival_dt").dt.weekday().alias("day_of_week"),
            pl.col("arrival_dt").dt.date().alias("date"),
            pl.col("arrival_dt").dt.day().is_in([1, 2, 3, 28, 29, 30, 31]).cast(pl.Int32).alias("is_month_end"),
            pl.col("arrival_dt").dt.hour().is_in([11, 12, 13, 14]).cast(pl.Int32).alias("is_peak_window")
        ])
        return df

    def compute_hourly_queue_metrics(self, df_tokens: pl.DataFrame, df_branches: pl.DataFrame) -> pl.DataFrame:
        """
        Aggregates tokens into hourly branch-level queue metrics:
        - Arrival rate Lambda
        - Service rate Mu per active counter
        - Counter utilization Rho = Lambda / (c * Mu)
        - SLA breach rates and digital deflection potential
        """
        grouped = df_tokens.group_by(["branch_id", "date", "arrival_hour"]).agg([
            pl.len().alias("total_arrivals"),
            pl.col("wait_time_minutes").mean().alias("avg_wait_minutes"),
            pl.col("wait_time_minutes").median().alias("median_wait_minutes"),
            pl.col("wait_time_minutes").max().alias("max_wait_minutes"),
            pl.col("service_duration_minutes").mean().alias("avg_service_minutes"),
            pl.col("sla_breached").sum().alias("sla_breaches"),
            pl.col("digital_deflectable").sum().alias("digital_deflectable_count"),
            pl.col("counter_id").n_unique().alias("unique_counters_active"),
            pl.col("staff_id").n_unique().alias("unique_staff_active"),
            pl.col("satisfaction_score").mean().alias("avg_satisfaction")
        ])

        merged = grouped.join(
            df_branches.select(["branch_id", "name", "total_counters"]),
            on="branch_id",
            how="left"
        )

        merged = merged.with_columns([
            (60.0 / pl.col("avg_service_minutes").clip(1.0, 60.0)).alias("mu_per_counter"),
            pl.col("unique_counters_active").clip(1, 20).alias("c_active")
        ])

        merged = merged.with_columns([
            (pl.col("total_arrivals") / (pl.col("c_active") * pl.col("mu_per_counter"))).clip(0.05, 1.95).alias("utilization_rho"),
            (pl.col("sla_breaches") / pl.col("total_arrivals")).alias("sla_breach_rate"),
            (pl.col("digital_deflectable_count") / pl.col("total_arrivals")).alias("digital_deflection_rate")
        ])

        return merged

    def run_pipeline(self):
        """Executes full pipeline and writes processed datasets."""
        tokens, staff, branches, feedback, appointments = self.load_raw_data()
        clean_tokens = self.preprocess_tokens(tokens)
        hourly_metrics = self.compute_hourly_queue_metrics(clean_tokens, branches)

        clean_tokens.write_csv(self.processed_dir / "clean_tokens.csv")
        hourly_metrics.write_csv(self.processed_dir / "hourly_queue_metrics.csv")
        print(f" Data Pipeline Complete: Processed {len(clean_tokens)} tokens and {len(hourly_metrics)} hourly windows.")
        return clean_tokens, hourly_metrics, staff, branches, feedback, appointments

if __name__ == "__main__":
    pipeline = BankingDataPipeline()
    pipeline.run_pipeline()
