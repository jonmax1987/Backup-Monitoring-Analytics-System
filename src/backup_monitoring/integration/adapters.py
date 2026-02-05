"""Adapter interfaces for integration layer."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from backup_monitoring.processing.models import AggregatedMetrics, DailyMetrics, WeeklyMetrics, MonthlyMetrics
from backup_monitoring.processing.comparison import PeriodComparison
from backup_monitoring.anomaly_detection.models import AnomalyDetectionResult
from backup_monitoring.data_loader.models import BackupRecord


class DataAdapter(ABC):
    """Base adapter interface for accessing processed data."""
    
    @abstractmethod
    def get_backup_records(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        backup_type: Optional[str] = None
    ) -> List[BackupRecord]:
        """
        Get backup records.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            backup_type: Optional backup type filter
            
        Returns:
            List of BackupRecord objects
        """
        pass
    
    @abstractmethod
    def get_daily_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        backup_type: Optional[str] = None
    ) -> List[DailyMetrics]:
        """
        Get daily aggregated metrics.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            backup_type: Optional backup type filter
            
        Returns:
            List of DailyMetrics objects
        """
        pass
    
    @abstractmethod
    def get_weekly_metrics(
        self,
        week_start: Optional[date] = None,
        backup_type: Optional[str] = None
    ) -> List[WeeklyMetrics]:
        """
        Get weekly aggregated metrics.
        
        Args:
            week_start: Optional week start date filter
            backup_type: Optional backup type filter
            
        Returns:
            List of WeeklyMetrics objects
        """
        pass
    
    @abstractmethod
    def get_monthly_metrics(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        backup_type: Optional[str] = None
    ) -> List[MonthlyMetrics]:
        """
        Get monthly aggregated metrics.
        
        Args:
            year: Optional year filter
            month: Optional month filter (1-12)
            backup_type: Optional backup type filter
            
        Returns:
            List of MonthlyMetrics objects
        """
        pass
    
    @abstractmethod
    def get_comparisons(
        self,
        period_type: str,
        backup_type: Optional[str] = None
    ) -> List[PeriodComparison]:
        """
        Get period comparisons.
        
        Args:
            period_type: Type of period ("day", "week", "month")
            backup_type: Optional backup type filter
            
        Returns:
            List of PeriodComparison objects
        """
        pass
    
    @abstractmethod
    def get_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        backup_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[AnomalyDetectionResult]:
        """
        Get anomaly detection results.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            backup_type: Optional backup type filter
            severity: Optional severity filter ("low", "medium", "high", "critical")
            
        Returns:
            List of AnomalyDetectionResult objects
        """
        pass


class UIAdapter(DataAdapter):
    """Adapter interface for UI integration."""
    
    @abstractmethod
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get summary data for dashboard.
        
        Returns:
            Dictionary with dashboard summary data
        """
        pass
    
    @abstractmethod
    def get_backup_types(self) -> List[str]:
        """
        Get list of available backup types.
        
        Returns:
            List of backup type strings
        """
        pass
    
    @abstractmethod
    def get_date_range(self) -> Dict[str, date]:
        """
        Get available date range.
        
        Returns:
            Dictionary with 'start' and 'end' dates
        """
        pass


class MonitoringAdapter(ABC):
    """Adapter interface for monitoring systems (Prometheus, Grafana)."""
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """
        Get metrics in format suitable for monitoring systems.
        
        Returns:
            Dictionary mapping metric names to values
        """
        pass
    
    @abstractmethod
    def get_metric_labels(self) -> Dict[str, Dict[str, str]]:
        """
        Get metrics with labels for Prometheus/Grafana.
        
        Returns:
            Dictionary mapping metric names to label dictionaries
        """
        pass
    
    @abstractmethod
    def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            String in Prometheus exposition format
        """
        pass
