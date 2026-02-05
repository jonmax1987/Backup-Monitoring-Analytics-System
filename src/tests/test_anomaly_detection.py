"""Tests for anomaly detection engine."""

import pytest
from datetime import date, timedelta
import statistics

from backup_monitoring.anomaly_detection.detector import AnomalyDetector, AnomalyDetectionError
from backup_monitoring.anomaly_detection.models import (
    Anomaly,
    AnomalyType,
    AnomalySeverity,
    AnomalyDetectionResult,
)
from backup_monitoring.processing.models import (
    DailyMetrics,
    PeriodType,
    AggregatedMetrics,
)


@pytest.fixture
def detector():
    """Create an AnomalyDetector instance."""
    return AnomalyDetector()


@pytest.fixture
def historical_metrics():
    """Create historical metrics for testing."""
    base_date = date(2024, 1, 1)
    
    return [
        DailyMetrics(
            period_start=base_date + timedelta(days=i),
            period_end=base_date + timedelta(days=i),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=base_date + timedelta(days=i),
            average_duration=1800.0,  # 30 minutes
            max_duration=3600.0,  # 1 hour
            min_duration=900.0,  # 15 minutes
            total_duration=1800.0,
            total_count=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
        )
        for i in range(7)  # 7 days of history
    ]


@pytest.fixture
def current_metrics_normal():
    """Create current metrics within normal range."""
    return DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 8),
        average_duration=1900.0,  # Slightly above average but within threshold
        max_duration=3700.0,
        min_duration=950.0,
        total_duration=1900.0,
        total_count=5,
        success_count=5,
        failure_count=0,
        partial_count=0,
    )


@pytest.fixture
def current_metrics_anomalous():
    """Create current metrics with anomalies."""
    return DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 8),
        average_duration=5000.0,  # Much higher than average (threshold is 2x = 3600)
        max_duration=8000.0,
        min_duration=2000.0,
        total_duration=5000.0,
        total_count=15,  # Much higher than average (threshold is 2x = 10)
        success_count=10,
        failure_count=5,  # High failure rate
        partial_count=0,
    )


def test_detect_anomalies_normal(detector, current_metrics_normal, historical_metrics):
    """Test that normal metrics don't trigger anomalies."""
    result = detector.detect_anomalies(current_metrics_normal, historical_metrics)
    
    assert result.has_anomaly is False
    assert len(result.anomalies) == 0
    assert result.samples_used == 7


def test_detect_anomalies_duration_high(detector, current_metrics_anomalous, historical_metrics):
    """Test detection of high duration anomaly."""
    result = detector.detect_anomalies(current_metrics_anomalous, historical_metrics)
    
    assert result.has_anomaly is True
    
    # Should detect average_duration anomaly
    duration_anomalies = [a for a in result.anomalies if a.metric_name == "average_duration"]
    assert len(duration_anomalies) > 0
    
    avg_anomaly = duration_anomalies[0]
    assert avg_anomaly.anomaly_type == AnomalyType.DURATION_HIGH
    assert avg_anomaly.current_value == 5000.0
    assert avg_anomaly.expected_value == 1800.0
    assert avg_anomaly.deviation_percentage > 100  # More than 100% increase


def test_detect_anomalies_duration_low(detector, historical_metrics):
    """Test detection of low duration anomaly."""
    current = DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 8),
        average_duration=500.0,  # Much lower than average (threshold is 0.5x = 900)
        max_duration=1000.0,
        min_duration=200.0,
        total_duration=500.0,
        total_count=5,
        success_count=5,
        failure_count=0,
        partial_count=0,
    )
    
    result = detector.detect_anomalies(current, historical_metrics)
    
    assert result.has_anomaly is True
    
    duration_anomalies = [a for a in result.anomalies if a.metric_name == "average_duration"]
    assert len(duration_anomalies) > 0
    assert duration_anomalies[0].anomaly_type == AnomalyType.DURATION_LOW


def test_detect_anomalies_count_high(detector, current_metrics_anomalous, historical_metrics):
    """Test detection of high count anomaly."""
    result = detector.detect_anomalies(current_metrics_anomalous, historical_metrics)
    
    assert result.has_anomaly is True
    
    count_anomalies = [a for a in result.anomalies if a.metric_name == "total_count"]
    assert len(count_anomalies) > 0
    
    count_anomaly = count_anomalies[0]
    assert count_anomaly.anomaly_type == AnomalyType.COUNT_HIGH
    assert count_anomaly.current_value == 15.0
    assert count_anomaly.expected_value == 5.0


def test_detect_anomalies_failure_rate_high(detector, current_metrics_anomalous, historical_metrics):
    """Test detection of high failure rate anomaly."""
    result = detector.detect_anomalies(current_metrics_anomalous, historical_metrics)
    
    assert result.has_anomaly is True
    
    failure_rate_anomalies = [a for a in result.anomalies if a.metric_name == "failure_rate"]
    assert len(failure_rate_anomalies) > 0
    
    failure_anomaly = failure_rate_anomalies[0]
    assert failure_anomaly.anomaly_type == AnomalyType.FAILURE_RATE_HIGH
    assert failure_anomaly.current_value > 0  # Has failures


def test_detect_anomalies_insufficient_samples(detector, current_metrics_normal):
    """Test that insufficient samples don't trigger detection."""
    # Only 2 samples (less than min_samples=5)
    historical = [
        DailyMetrics(
            period_start=date(2024, 1, i),
            period_end=date(2024, 1, i),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=date(2024, 1, i),
            average_duration=1800.0,
            max_duration=3600.0,
            min_duration=900.0,
            total_duration=1800.0,
            total_count=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
        )
        for i in range(1, 3)
    ]
    
    result = detector.detect_anomalies(current_metrics_normal, historical)
    
    assert result.has_anomaly is False
    assert result.samples_used == 2


def test_detect_anomalies_empty_history(detector, current_metrics_normal):
    """Test detection with empty history."""
    result = detector.detect_anomalies(current_metrics_normal, [])
    
    assert result.has_anomaly is False
    assert result.samples_used == 0


def test_detect_anomalies_different_backup_type(detector, current_metrics_normal, historical_metrics):
    """Test that different backup types are filtered out."""
    # Current metrics have different backup type
    current = DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="filesystem",  # Different backup type
        period_date=date(2024, 1, 8),
        average_duration=5000.0,  # Would be anomaly if same type
        max_duration=8000.0,
        min_duration=2000.0,
        total_duration=5000.0,
        total_count=15,
        success_count=10,
        failure_count=5,
        partial_count=0,
    )
    
    result = detector.detect_anomalies(current, historical_metrics)
    
    # Should have no anomalies because historical data is filtered out
    assert result.has_anomaly is False
    assert result.samples_used == 0


def test_detect_anomalies_max_duration(detector, historical_metrics):
    """Test detection of max duration anomaly."""
    current = DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 8),
        average_duration=1800.0,  # Normal average
        max_duration=8000.0,  # Very high max (threshold is 2x = 7200)
        min_duration=900.0,
        total_duration=1800.0,
        total_count=5,
        success_count=5,
        failure_count=0,
        partial_count=0,
    )
    
    result = detector.detect_anomalies(current, historical_metrics)
    
    assert result.has_anomaly is True
    
    max_duration_anomalies = [a for a in result.anomalies if a.metric_name == "max_duration"]
    assert len(max_duration_anomalies) > 0


def test_detect_anomalies_success_rate_low(detector, historical_metrics):
    """Test detection of low success rate anomaly."""
    current = DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 8),
        average_duration=1800.0,
        max_duration=3600.0,
        min_duration=900.0,
        total_duration=1800.0,
        total_count=10,
        success_count=3,  # Only 30% success (threshold is 0.5x = 50%)
        failure_count=7,
        partial_count=0,
    )
    
    result = detector.detect_anomalies(current, historical_metrics)
    
    assert result.has_anomaly is True
    
    success_rate_anomalies = [a for a in result.anomalies if a.metric_name == "success_rate"]
    assert len(success_rate_anomalies) > 0
    assert success_rate_anomalies[0].anomaly_type == AnomalyType.SUCCESS_RATE_LOW


def test_severity_calculation(detector, historical_metrics):
    """Test that severity is calculated correctly."""
    # Critical anomaly (>200% deviation)
    current = DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 8),
        average_duration=6000.0,  # 233% increase
        max_duration=8000.0,
        min_duration=2000.0,
        total_duration=6000.0,
        total_count=5,
        success_count=5,
        failure_count=0,
        partial_count=0,
    )
    
    result = detector.detect_anomalies(current, historical_metrics)
    
    assert result.has_anomaly is True
    # Should have at least one critical or high severity anomaly
    assert any(a.severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH] for a in result.anomalies)


def test_detect_batch(detector, historical_metrics):
    """Test batch anomaly detection."""
    # Add current metrics to the list
    metrics_list = historical_metrics + [
        DailyMetrics(
            period_start=date(2024, 1, 8),
            period_end=date(2024, 1, 8),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=date(2024, 1, 8),
            average_duration=5000.0,  # Anomalous
            max_duration=8000.0,
            min_duration=2000.0,
            total_duration=5000.0,
            total_count=15,
            success_count=10,
            failure_count=5,
            partial_count=0,
        )
    ]
    
    results = detector.detect_batch(metrics_list)
    
    assert len(results) == len(metrics_list)
    
    # First few should have no anomalies (not enough history)
    assert results[0].has_anomaly is False
    
    # Last one should have anomalies
    assert results[-1].has_anomaly is True


def test_anomaly_properties():
    """Test Anomaly model properties."""
    anomaly = Anomaly(
        anomaly_type=AnomalyType.DURATION_HIGH,
        severity=AnomalySeverity.CRITICAL,
        metric_name="average_duration",
        current_value=5000.0,
        expected_value=1800.0,
        threshold_value=3600.0,
        deviation_percentage=177.78,
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        backup_type="database",
        period_type="day",
    )
    
    assert anomaly.is_critical is True


def test_anomaly_detection_result_properties():
    """Test AnomalyDetectionResult properties."""
    anomalies = [
        Anomaly(
            anomaly_type=AnomalyType.DURATION_HIGH,
            severity=AnomalySeverity.CRITICAL,
            metric_name="average_duration",
            current_value=5000.0,
            expected_value=1800.0,
            threshold_value=3600.0,
            deviation_percentage=177.78,
            period_start=date(2024, 1, 8),
            period_end=date(2024, 1, 8),
            backup_type="database",
            period_type="day",
        ),
        Anomaly(
            anomaly_type=AnomalyType.COUNT_HIGH,
            severity=AnomalySeverity.MEDIUM,
            metric_name="total_count",
            current_value=15.0,
            expected_value=5.0,
            threshold_value=10.0,
            deviation_percentage=200.0,
            period_start=date(2024, 1, 8),
            period_end=date(2024, 1, 8),
            backup_type="database",
            period_type="day",
        ),
    ]
    
    current_metrics = DailyMetrics(
        period_start=date(2024, 1, 8),
        period_end=date(2024, 1, 8),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 8),
        average_duration=5000.0,
        max_duration=8000.0,
        min_duration=2000.0,
        total_duration=5000.0,
        total_count=15,
        success_count=10,
        failure_count=5,
        partial_count=0,
    )
    
    result = AnomalyDetectionResult(
        has_anomaly=True,
        anomalies=anomalies,
        metrics=current_metrics,
        historical_average=1800.0,
        samples_used=7,
    )
    
    assert result.anomaly_count == 2
    assert len(result.critical_anomalies) == 1
    assert result.critical_anomalies[0].severity == AnomalySeverity.CRITICAL


def test_lookback_periods_limit(detector, historical_metrics):
    """Test that lookback periods limit is respected."""
    # Create more historical metrics than lookback_periods (7)
    extended_history = historical_metrics + [
        DailyMetrics(
            period_start=date(2024, 1, i),
            period_end=date(2024, 1, i),
            period_type=PeriodType.DAY,
            backup_type="database",
            period_date=date(2024, 1, i),
            average_duration=1800.0,
            max_duration=3600.0,
            min_duration=900.0,
            total_duration=1800.0,
            total_count=5,
            success_count=5,
            failure_count=0,
            partial_count=0,
        )
        for i in range(8, 15)  # 7 more days
    ]
    
    current = DailyMetrics(
        period_start=date(2024, 1, 15),
        period_end=date(2024, 1, 15),
        period_type=PeriodType.DAY,
        backup_type="database",
        period_date=date(2024, 1, 15),
        average_duration=5000.0,
        max_duration=8000.0,
        min_duration=2000.0,
        total_duration=5000.0,
        total_count=5,
        success_count=5,
        failure_count=0,
        partial_count=0,
    )
    
    result = detector.detect_anomalies(current, extended_history)
    
    # Should only use last 7 periods (lookback_periods)
    assert result.samples_used == 7
