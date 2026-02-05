"""Data provider for integration layer."""

from typing import List, Optional, Dict, Any
from datetime import date
from pathlib import Path

from backup_monitoring.integration.adapters import DataAdapter, UIAdapter, MonitoringAdapter
from backup_monitoring.processing.models import AggregatedMetrics, DailyMetrics, WeeklyMetrics, MonthlyMetrics
from backup_monitoring.processing.comparison import PeriodComparison
from backup_monitoring.anomaly_detection.models import AnomalyDetectionResult, AnomalySeverity
from backup_monitoring.data_loader.models import BackupRecord


class IntegrationDataProvider:
    """Provides processed data to integration adapters."""
    
    def __init__(
        self,
        backup_records: Optional[List[BackupRecord]] = None,
        daily_metrics: Optional[List[DailyMetrics]] = None,
        weekly_metrics: Optional[List[WeeklyMetrics]] = None,
        monthly_metrics: Optional[List[MonthlyMetrics]] = None,
        comparisons: Optional[List[PeriodComparison]] = None,
        anomalies: Optional[List[AnomalyDetectionResult]] = None,
    ):
        """
        Initialize the data provider.
        
        Args:
            backup_records: List of backup records
            daily_metrics: List of daily metrics
            weekly_metrics: List of weekly metrics
            monthly_metrics: List of monthly metrics
            comparisons: List of period comparisons
            anomalies: List of anomaly detection results
        """
        self.backup_records = backup_records or []
        self.daily_metrics = daily_metrics or []
        self.weekly_metrics = weekly_metrics or []
        self.monthly_metrics = monthly_metrics or []
        self.comparisons = comparisons or []
        self.anomalies = anomalies or []
    
    def update_data(
        self,
        backup_records: Optional[List[BackupRecord]] = None,
        daily_metrics: Optional[List[DailyMetrics]] = None,
        weekly_metrics: Optional[List[WeeklyMetrics]] = None,
        monthly_metrics: Optional[List[MonthlyMetrics]] = None,
        comparisons: Optional[List[PeriodComparison]] = None,
        anomalies: Optional[List[AnomalyDetectionResult]] = None,
    ) -> None:
        """Update the data in the provider."""
        if backup_records is not None:
            self.backup_records = backup_records
        if daily_metrics is not None:
            self.daily_metrics = daily_metrics
        if weekly_metrics is not None:
            self.weekly_metrics = weekly_metrics
        if monthly_metrics is not None:
            self.monthly_metrics = monthly_metrics
        if comparisons is not None:
            self.comparisons = comparisons
        if anomalies is not None:
            self.anomalies = anomalies


class StandardDataAdapter(DataAdapter):
    """Standard implementation of DataAdapter."""
    
    def __init__(self, data_provider: IntegrationDataProvider):
        """
        Initialize the adapter.
        
        Args:
            data_provider: Data provider instance
        """
        self.data_provider = data_provider
    
    def get_backup_records(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        backup_type: Optional[str] = None
    ) -> List[BackupRecord]:
        """Get filtered backup records."""
        records = self.data_provider.backup_records
        
        # Apply filters
        if start_date:
            records = [r for r in records if r.start_time.date() >= start_date]
        if end_date:
            records = [r for r in records if r.start_time.date() <= end_date]
        if backup_type:
            records = [r for r in records if r.backup_type == backup_type]
        
        return records
    
    def get_daily_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        backup_type: Optional[str] = None
    ) -> List[DailyMetrics]:
        """Get filtered daily metrics."""
        metrics = self.data_provider.daily_metrics
        
        # Apply filters
        if start_date:
            metrics = [m for m in metrics if m.period_date >= start_date]
        if end_date:
            metrics = [m for m in metrics if m.period_date <= end_date]
        if backup_type:
            metrics = [m for m in metrics if m.backup_type == backup_type]
        
        return metrics
    
    def get_weekly_metrics(
        self,
        week_start: Optional[date] = None,
        backup_type: Optional[str] = None
    ) -> List[WeeklyMetrics]:
        """Get filtered weekly metrics."""
        metrics = self.data_provider.weekly_metrics
        
        # Apply filters
        if week_start:
            metrics = [m for m in metrics if m.week_start == week_start]
        if backup_type:
            metrics = [m for m in metrics if m.backup_type == backup_type]
        
        return metrics
    
    def get_monthly_metrics(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        backup_type: Optional[str] = None
    ) -> List[MonthlyMetrics]:
        """Get filtered monthly metrics."""
        metrics = self.data_provider.monthly_metrics
        
        # Apply filters
        if year:
            metrics = [m for m in metrics if m.year == year]
        if month:
            metrics = [m for m in metrics if m.month == month]
        if backup_type:
            metrics = [m for m in metrics if m.backup_type == backup_type]
        
        return metrics
    
    def get_comparisons(
        self,
        period_type: str,
        backup_type: Optional[str] = None
    ) -> List[PeriodComparison]:
        """Get filtered comparisons."""
        comparisons = [
            c for c in self.data_provider.comparisons
            if c.period_type.value == period_type
        ]
        
        if backup_type:
            comparisons = [c for c in comparisons if c.backup_type == backup_type]
        
        return comparisons
    
    def get_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        backup_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[AnomalyDetectionResult]:
        """Get filtered anomalies."""
        anomalies = [
            a for a in self.data_provider.anomalies
            if a.has_anomaly
        ]
        
        # Apply filters
        if start_date:
            anomalies = [a for a in anomalies if a.metrics.period_start >= start_date]
        if end_date:
            anomalies = [a for a in anomalies if a.metrics.period_end <= end_date]
        if backup_type:
            anomalies = [a for a in anomalies if a.metrics.backup_type == backup_type]
        if severity:
            anomalies = [
                a for a in anomalies
                if any(anom.severity.value == severity for anom in a.anomalies)
            ]
        
        return anomalies


class StandardUIAdapter(StandardDataAdapter, UIAdapter):
    """Standard implementation of UIAdapter."""
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary data."""
        all_metrics = (
            self.data_provider.daily_metrics +
            self.data_provider.weekly_metrics +
            self.data_provider.monthly_metrics
        )
        
        total_backups = sum(m.total_count for m in all_metrics)
        total_success = sum(m.success_count for m in all_metrics)
        total_failure = sum(m.failure_count for m in all_metrics)
        
        critical_anomalies = sum(
            1 for a in self.data_provider.anomalies
            if a.has_anomaly and len(a.critical_anomalies) > 0
        )
        
        return {
            "total_backups": total_backups,
            "total_success": total_success,
            "total_failure": total_failure,
            "success_rate": (total_success / total_backups * 100) if total_backups > 0 else 0,
            "total_anomalies": sum(1 for a in self.data_provider.anomalies if a.has_anomaly),
            "critical_anomalies": critical_anomalies,
            "backup_types": self.get_backup_types(),
            "date_range": self.get_date_range(),
        }
    
    def get_backup_types(self) -> List[str]:
        """Get list of available backup types."""
        types = set()
        
        for record in self.data_provider.backup_records:
            if record.backup_type:
                types.add(record.backup_type)
        
        for metrics in [
            self.data_provider.daily_metrics,
            self.data_provider.weekly_metrics,
            self.data_provider.monthly_metrics,
        ]:
            for m in metrics:
                types.add(m.backup_type)
        
        return sorted(list(types))
    
    def get_date_range(self) -> Dict[str, date]:
        """Get available date range."""
        dates = []
        
        for record in self.data_provider.backup_records:
            dates.append(record.start_time.date())
        
        for metrics in [
            self.data_provider.daily_metrics,
            self.data_provider.weekly_metrics,
            self.data_provider.monthly_metrics,
        ]:
            for m in metrics:
                dates.append(m.period_start)
                dates.append(m.period_end)
        
        if not dates:
            return {"start": date.today(), "end": date.today()}
        
        return {
            "start": min(dates),
            "end": max(dates),
        }


class StandardMonitoringAdapter(MonitoringAdapter):
    """Standard implementation of MonitoringAdapter."""
    
    def __init__(self, data_provider: IntegrationDataProvider):
        """
        Initialize the adapter.
        
        Args:
            data_provider: Data provider instance
        """
        self.data_provider = data_provider
    
    def get_metrics(self) -> Dict[str, float]:
        """Get metrics as dictionary."""
        all_metrics = (
            self.data_provider.daily_metrics +
            self.data_provider.weekly_metrics +
            self.data_provider.monthly_metrics
        )
        
        if not all_metrics:
            return {}
        
        total_backups = sum(m.total_count for m in all_metrics)
        total_success = sum(m.success_count for m in all_metrics)
        total_failure = sum(m.failure_count for m in all_metrics)
        avg_duration = sum(m.average_duration for m in all_metrics) / len(all_metrics) if all_metrics else 0
        
        return {
            "backup_total": float(total_backups),
            "backup_success": float(total_success),
            "backup_failure": float(total_failure),
            "backup_success_rate": (total_success / total_backups * 100) if total_backups > 0 else 0,
            "backup_avg_duration_seconds": avg_duration,
            "anomaly_count": float(sum(1 for a in self.data_provider.anomalies if a.has_anomaly)),
            "anomaly_critical_count": float(sum(
                len(a.critical_anomalies) for a in self.data_provider.anomalies if a.has_anomaly
            )),
        }
    
    def get_metric_labels(self) -> Dict[str, Dict[str, str]]:
        """Get metrics with labels."""
        metrics = self.get_metrics()
        labeled = {}
        
        for metric_name, value in metrics.items():
            labeled[metric_name] = {
                "value": str(value),
                "labels": {
                    "system": "backup_monitoring",
                    "version": "1.0.0",
                }
            }
        
        return labeled
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        lines.append("# HELP backup_total Total number of backups")
        lines.append("# TYPE backup_total gauge")
        
        metrics = self.get_metrics()
        
        for metric_name, value in metrics.items():
            # Convert metric name to Prometheus format
            prom_name = metric_name.replace(".", "_")
            lines.append(f"{prom_name}{{system=\"backup_monitoring\"}} {value}")
        
        return "\n".join(lines)
