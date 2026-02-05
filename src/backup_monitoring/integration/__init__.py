"""Integration layer module for external systems."""

from backup_monitoring.integration.adapters import (
    DataAdapter,
    UIAdapter,
    MonitoringAdapter,
)
from backup_monitoring.integration.data_provider import (
    IntegrationDataProvider,
    StandardDataAdapter,
    StandardUIAdapter,
    StandardMonitoringAdapter,
)
from backup_monitoring.integration.mocks import (
    MockDataProvider,
    MockUIAdapter,
    MockMonitoringAdapter,
)

__all__ = [
    "DataAdapter",
    "UIAdapter",
    "MonitoringAdapter",
    "IntegrationDataProvider",
    "StandardDataAdapter",
    "StandardUIAdapter",
    "StandardMonitoringAdapter",
    "MockDataProvider",
    "MockUIAdapter",
    "MockMonitoringAdapter",
]
