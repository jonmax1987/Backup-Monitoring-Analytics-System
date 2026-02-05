"""Anomaly detection engine."""

from typing import List, Optional, Dict, Any
from datetime import date
import statistics

from backup_monitoring.config.config_loader import get_config
from backup_monitoring.processing.models import AggregatedMetrics, PeriodType
from backup_monitoring.anomaly_detection.models import (
    Anomaly,
    AnomalyType,
    AnomalySeverity,
    AnomalyDetectionResult,
)


class AnomalyDetectionError(Exception):
    """Exception raised when anomaly detection fails."""
    pass


class AnomalyDetector:
    """Rule-based anomaly detection engine."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the anomaly detector.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = get_config(config_path)
        self.enabled = self.config.anomaly_detection.enabled
        self.threshold_multiplier = self.config.anomaly_detection.threshold_multiplier
        self.min_samples = self.config.anomaly_detection.min_samples
        self.lookback_periods = self.config.anomaly_detection.lookback_periods
    
    def detect_anomalies(
        self,
        current_metrics: AggregatedMetrics,
        historical_metrics: List[AggregatedMetrics]
    ) -> AnomalyDetectionResult:
        """
        Detect anomalies in current metrics compared to historical data.
        
        Args:
            current_metrics: Current period metrics to analyze
            historical_metrics: List of historical metrics for comparison
            
        Returns:
            AnomalyDetectionResult with detected anomalies
        """
        if not self.enabled:
            return AnomalyDetectionResult(
                has_anomaly=False,
                metrics=current_metrics,
                historical_average=None,
                samples_used=0,
            )
        
        # Filter historical metrics by backup type and period type
        filtered_history = self._filter_historical_metrics(
            historical_metrics,
            current_metrics.backup_type,
            current_metrics.period_type
        )
        
        # Limit to lookback periods
        filtered_history = filtered_history[-self.lookback_periods:]
        
        # Check if we have enough samples
        if len(filtered_history) < self.min_samples:
            return AnomalyDetectionResult(
                has_anomaly=False,
                metrics=current_metrics,
                historical_average=None,
                samples_used=len(filtered_history),
            )
        
        anomalies = []
        
        # Detect duration anomalies
        duration_anomalies = self._detect_duration_anomalies(
            current_metrics,
            filtered_history
        )
        anomalies.extend(duration_anomalies)
        
        # Detect count anomalies
        count_anomalies = self._detect_count_anomalies(
            current_metrics,
            filtered_history
        )
        anomalies.extend(count_anomalies)
        
        # Detect rate anomalies
        rate_anomalies = self._detect_rate_anomalies(
            current_metrics,
            filtered_history
        )
        anomalies.extend(rate_anomalies)
        
        # Calculate historical average for average_duration
        historical_avg_duration = statistics.mean(
            [m.average_duration for m in filtered_history]
        ) if filtered_history else None
        
        return AnomalyDetectionResult(
            has_anomaly=len(anomalies) > 0,
            anomalies=anomalies,
            metrics=current_metrics,
            historical_average=historical_avg_duration,
            samples_used=len(filtered_history),
        )
    
    def _filter_historical_metrics(
        self,
        historical_metrics: List[AggregatedMetrics],
        backup_type: str,
        period_type: PeriodType
    ) -> List[AggregatedMetrics]:
        """Filter historical metrics by backup type and period type."""
        return [
            m for m in historical_metrics
            if m.backup_type == backup_type and m.period_type == period_type
        ]
    
    def _detect_duration_anomalies(
        self,
        current: AggregatedMetrics,
        historical: List[AggregatedMetrics]
    ) -> List[Anomaly]:
        """Detect anomalies in duration metrics."""
        anomalies = []
        
        # Average duration anomaly
        historical_avg = statistics.mean([m.average_duration for m in historical])
        historical_stdev = statistics.stdev([m.average_duration for m in historical]) if len(historical) > 1 else 0
        
        threshold_high = historical_avg * self.threshold_multiplier
        threshold_low = historical_avg / self.threshold_multiplier
        
        if current.average_duration > threshold_high:
            deviation = ((current.average_duration - historical_avg) / historical_avg) * 100
            severity = self._calculate_severity(deviation, historical_stdev, historical_avg)
            
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.DURATION_HIGH,
                severity=severity,
                metric_name="average_duration",
                current_value=current.average_duration,
                expected_value=historical_avg,
                threshold_value=threshold_high,
                deviation_percentage=deviation,
                period_start=current.period_start,
                period_end=current.period_end,
                backup_type=current.backup_type,
                period_type=current.period_type.value,
            ))
        
        elif current.average_duration < threshold_low and historical_avg > 0:
            deviation = ((historical_avg - current.average_duration) / historical_avg) * 100
            severity = self._calculate_severity(deviation, historical_stdev, historical_avg)
            
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.DURATION_LOW,
                severity=severity,
                metric_name="average_duration",
                current_value=current.average_duration,
                expected_value=historical_avg,
                threshold_value=threshold_low,
                deviation_percentage=-deviation,
                period_start=current.period_start,
                period_end=current.period_end,
                backup_type=current.backup_type,
                period_type=current.period_type.value,
            ))
        
        # Max duration anomaly
        historical_max_avg = statistics.mean([m.max_duration for m in historical])
        max_threshold = historical_max_avg * self.threshold_multiplier
        
        if current.max_duration > max_threshold:
            deviation = ((current.max_duration - historical_max_avg) / historical_max_avg) * 100
            severity = self._calculate_severity(deviation, 0, historical_max_avg)
            
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.DURATION_HIGH,
                severity=severity,
                metric_name="max_duration",
                current_value=current.max_duration,
                expected_value=historical_max_avg,
                threshold_value=max_threshold,
                deviation_percentage=deviation,
                period_start=current.period_start,
                period_end=current.period_end,
                backup_type=current.backup_type,
                period_type=current.period_type.value,
            ))
        
        return anomalies
    
    def _detect_count_anomalies(
        self,
        current: AggregatedMetrics,
        historical: List[AggregatedMetrics]
    ) -> List[Anomaly]:
        """Detect anomalies in count metrics."""
        anomalies = []
        
        # Total count anomaly
        historical_counts = [m.total_count for m in historical]
        historical_avg = statistics.mean(historical_counts)
        
        if historical_avg == 0:
            # If historical average is zero, any count is an anomaly
            if current.total_count > 0:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.COUNT_HIGH,
                    severity=AnomalySeverity.MEDIUM,
                    metric_name="total_count",
                    current_value=float(current.total_count),
                    expected_value=0.0,
                    threshold_value=0.0,
                    deviation_percentage=100.0,
                    period_start=current.period_start,
                    period_end=current.period_end,
                    backup_type=current.backup_type,
                    period_type=current.period_type.value,
                ))
            return anomalies
        
        threshold_high = historical_avg * self.threshold_multiplier
        threshold_low = historical_avg / self.threshold_multiplier
        
        if current.total_count > threshold_high:
            deviation = ((current.total_count - historical_avg) / historical_avg) * 100
            severity = self._calculate_severity(deviation, 0, historical_avg)
            
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.COUNT_HIGH,
                severity=severity,
                metric_name="total_count",
                current_value=float(current.total_count),
                expected_value=historical_avg,
                threshold_value=threshold_high,
                deviation_percentage=deviation,
                period_start=current.period_start,
                period_end=current.period_end,
                backup_type=current.backup_type,
                period_type=current.period_type.value,
            ))
        
        elif current.total_count < threshold_low:
            deviation = ((historical_avg - current.total_count) / historical_avg) * 100
            severity = self._calculate_severity(deviation, 0, historical_avg)
            
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.COUNT_LOW,
                severity=severity,
                metric_name="total_count",
                current_value=float(current.total_count),
                expected_value=historical_avg,
                threshold_value=threshold_low,
                deviation_percentage=-deviation,
                period_start=current.period_start,
                period_end=current.period_end,
                backup_type=current.backup_type,
                period_type=current.period_type.value,
            ))
        
        return anomalies
    
    def _detect_rate_anomalies(
        self,
        current: AggregatedMetrics,
        historical: List[AggregatedMetrics]
    ) -> List[Anomaly]:
        """Detect anomalies in success/failure rates."""
        anomalies = []
        
        # Failure rate anomaly
        historical_failure_rates = [m.failure_rate for m in historical]
        historical_avg_failure_rate = statistics.mean(historical_failure_rates)
        
        # If failure rate is significantly higher than historical average
        if historical_avg_failure_rate == 0:
            # Any failure is an anomaly if historical average is zero
            if current.failure_rate > 0:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.FAILURE_RATE_HIGH,
                    severity=AnomalySeverity.HIGH,
                    metric_name="failure_rate",
                    current_value=current.failure_rate,
                    expected_value=0.0,
                    threshold_value=0.0,
                    deviation_percentage=100.0,
                    period_start=current.period_start,
                    period_end=current.period_end,
                    backup_type=current.backup_type,
                    period_type=current.period_type.value,
                ))
        else:
            threshold = historical_avg_failure_rate * self.threshold_multiplier
            if current.failure_rate > threshold:
                deviation = ((current.failure_rate - historical_avg_failure_rate) / historical_avg_failure_rate) * 100
                severity = self._calculate_severity(deviation, 0, historical_avg_failure_rate)
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.FAILURE_RATE_HIGH,
                    severity=severity,
                    metric_name="failure_rate",
                    current_value=current.failure_rate,
                    expected_value=historical_avg_failure_rate,
                    threshold_value=threshold,
                    deviation_percentage=deviation,
                    period_start=current.period_start,
                    period_end=current.period_end,
                    backup_type=current.backup_type,
                    period_type=current.period_type.value,
                ))
        
        # Success rate anomaly (inverse of failure rate)
        historical_success_rates = [m.success_rate for m in historical]
        historical_avg_success_rate = statistics.mean(historical_success_rates)
        
        if historical_avg_success_rate > 0:
            threshold = historical_avg_success_rate / self.threshold_multiplier
            if current.success_rate < threshold:
                deviation = ((historical_avg_success_rate - current.success_rate) / historical_avg_success_rate) * 100
                severity = self._calculate_severity(deviation, 0, historical_avg_success_rate)
                
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.SUCCESS_RATE_LOW,
                    severity=severity,
                    metric_name="success_rate",
                    current_value=current.success_rate,
                    expected_value=historical_avg_success_rate,
                    threshold_value=threshold,
                    deviation_percentage=-deviation,
                    period_start=current.period_start,
                    period_end=current.period_end,
                    backup_type=current.backup_type,
                    period_type=current.period_type.value,
                ))
        
        return anomalies
    
    def _calculate_severity(
        self,
        deviation_percentage: float,
        standard_deviation: float,
        average_value: float
    ) -> AnomalySeverity:
        """
        Calculate anomaly severity based on deviation.
        
        Args:
            deviation_percentage: Percentage deviation from expected
            standard_deviation: Standard deviation of historical values
            average_value: Average historical value
            
        Returns:
            AnomalySeverity level
        """
        abs_deviation = abs(deviation_percentage)
        
        # Use standard deviation if available
        if standard_deviation > 0 and average_value > 0:
            z_score = abs_deviation / (standard_deviation / average_value * 100)
            if z_score >= 3:
                return AnomalySeverity.CRITICAL
            elif z_score >= 2:
                return AnomalySeverity.HIGH
            elif z_score >= 1:
                return AnomalySeverity.MEDIUM
        
        # Fallback to percentage-based severity
        if abs_deviation >= 200:
            return AnomalySeverity.CRITICAL
        elif abs_deviation >= 100:
            return AnomalySeverity.HIGH
        elif abs_deviation >= 50:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def detect_batch(
        self,
        metrics_list: List[AggregatedMetrics]
    ) -> List[AnomalyDetectionResult]:
        """
        Detect anomalies for a batch of metrics.
        
        Args:
            metrics_list: List of metrics ordered chronologically
            
        Returns:
            List of AnomalyDetectionResult objects
        """
        results = []
        
        for i, current_metrics in enumerate(metrics_list):
            # Use previous metrics as historical data
            historical = metrics_list[:i]
            
            result = self.detect_anomalies(current_metrics, historical)
            results.append(result)
        
        return results
