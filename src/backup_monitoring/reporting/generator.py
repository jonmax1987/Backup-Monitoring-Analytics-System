"""Report generator for backup monitoring system."""

import json
import csv
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from io import StringIO

from backup_monitoring.config.config_loader import get_config
from backup_monitoring.processing.models import AggregatedMetrics, DailyMetrics, WeeklyMetrics, MonthlyMetrics
from backup_monitoring.processing.comparison import PeriodComparison
from backup_monitoring.anomaly_detection.models import AnomalyDetectionResult


class ReportGenerationError(Exception):
    """Exception raised when report generation fails."""
    pass


class ReportGenerator:
    """Generates reports in multiple formats (JSON, CSV, HTML)."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the report generator.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = get_config(config_path)
        self.output_directory = Path(self.config.reporting.output_directory)
        self.supported_formats = self.config.reporting.formats
        self.date_format = self.config.reporting.date_format
    
    def generate_daily_report(
        self,
        daily_metrics: List[DailyMetrics],
        anomalies: Optional[List[AnomalyDetectionResult]] = None,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """
        Generate daily report.
        
        Args:
            daily_metrics: List of daily metrics
            anomalies: Optional list of anomaly detection results
            formats: Optional list of formats (defaults to config)
            
        Returns:
            Dictionary mapping format to file path
        """
        formats = formats or self.supported_formats
        output_files = {}
        
        # Prepare report data
        report_data = self._prepare_daily_report_data(daily_metrics, anomalies)
        
        # Generate in requested formats
        if "json" in formats:
            output_files["json"] = self._generate_json_report(report_data, "daily")
        
        if "csv" in formats:
            output_files["csv"] = self._generate_csv_report(report_data, "daily")
        
        if "html" in formats:
            output_files["html"] = self._generate_html_report(report_data, "daily")
        
        return output_files
    
    def generate_period_report(
        self,
        metrics: List[AggregatedMetrics],
        period_type: str,
        comparisons: Optional[List[PeriodComparison]] = None,
        anomalies: Optional[List[AnomalyDetectionResult]] = None,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """
        Generate period-based report (week/month).
        
        Args:
            metrics: List of aggregated metrics
            period_type: Type of period ("week" or "month")
            comparisons: Optional list of period comparisons
            anomalies: Optional list of anomaly detection results
            formats: Optional list of formats (defaults to config)
            
        Returns:
            Dictionary mapping format to file path
        """
        formats = formats or self.supported_formats
        output_files = {}
        
        # Prepare report data
        report_data = self._prepare_period_report_data(metrics, period_type, comparisons, anomalies)
        
        # Generate in requested formats
        if "json" in formats:
            output_files["json"] = self._generate_json_report(report_data, period_type)
        
        if "csv" in formats:
            output_files["csv"] = self._generate_csv_report(report_data, period_type)
        
        if "html" in formats:
            output_files["html"] = self._generate_html_report(report_data, period_type)
        
        return output_files
    
    def generate_comparison_report(
        self,
        comparisons: List[PeriodComparison],
        formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """
        Generate historical comparison report.
        
        Args:
            comparisons: List of period comparisons
            formats: Optional list of formats (defaults to config)
            
        Returns:
            Dictionary mapping format to file path
        """
        formats = formats or self.supported_formats
        output_files = {}
        
        # Prepare report data
        report_data = self._prepare_comparison_report_data(comparisons)
        
        # Generate in requested formats
        if "json" in formats:
            output_files["json"] = self._generate_json_report(report_data, "comparison")
        
        if "csv" in formats:
            output_files["csv"] = self._generate_csv_report(report_data, "comparison")
        
        if "html" in formats:
            output_files["html"] = self._generate_html_report(report_data, "comparison")
        
        return output_files
    
    def _prepare_daily_report_data(
        self,
        daily_metrics: List[DailyMetrics],
        anomalies: Optional[List[AnomalyDetectionResult]]
    ) -> Dict[str, Any]:
        """Prepare data structure for daily report."""
        return {
            "report_type": "daily",
            "generated_at": datetime.now().isoformat(),
            "metrics": [self._metric_to_dict(m) for m in daily_metrics],
            "anomalies": [self._anomaly_result_to_dict(a) for a in (anomalies or [])],
            "summary": self._calculate_summary(daily_metrics),
        }
    
    def _prepare_period_report_data(
        self,
        metrics: List[AggregatedMetrics],
        period_type: str,
        comparisons: Optional[List[PeriodComparison]],
        anomalies: Optional[List[AnomalyDetectionResult]]
    ) -> Dict[str, Any]:
        """Prepare data structure for period report."""
        return {
            "report_type": period_type,
            "generated_at": datetime.now().isoformat(),
            "metrics": [self._metric_to_dict(m) for m in metrics],
            "comparisons": [self._comparison_to_dict(c) for c in (comparisons or [])],
            "anomalies": [self._anomaly_result_to_dict(a) for a in (anomalies or [])],
            "summary": self._calculate_summary(metrics),
        }
    
    def _prepare_comparison_report_data(
        self,
        comparisons: List[PeriodComparison]
    ) -> Dict[str, Any]:
        """Prepare data structure for comparison report."""
        return {
            "report_type": "comparison",
            "generated_at": datetime.now().isoformat(),
            "comparisons": [self._comparison_to_dict(c) for c in comparisons],
            "summary": {
                "total_comparisons": len(comparisons),
                "periods_with_changes": sum(1 for c in comparisons if len(c.all_deltas) > 0),
            },
        }
    
    def _metric_to_dict(self, metric: AggregatedMetrics) -> Dict[str, Any]:
        """Convert AggregatedMetrics to dictionary."""
        base = {
            "period_start": metric.period_start.isoformat(),
            "period_end": metric.period_end.isoformat(),
            "period_type": metric.period_type.value,
            "backup_type": metric.backup_type,
            "average_duration": metric.average_duration,
            "max_duration": metric.max_duration,
            "min_duration": metric.min_duration,
            "total_duration": metric.total_duration,
            "total_count": metric.total_count,
            "success_count": metric.success_count,
            "failure_count": metric.failure_count,
            "partial_count": metric.partial_count,
            "success_rate": metric.success_rate,
            "failure_rate": metric.failure_rate,
            "anomaly_flag": metric.anomaly_flag,
        }
        
        # Add period-specific fields
        if isinstance(metric, DailyMetrics):
            base["date"] = metric.date.isoformat()
        elif isinstance(metric, WeeklyMetrics):
            base["week_start"] = metric.week_start.isoformat()
            base["week_end"] = metric.week_end.isoformat()
            base["week_number"] = metric.week_number
        elif isinstance(metric, MonthlyMetrics):
            base["year"] = metric.year
            base["month"] = metric.month
        
        return base
    
    def _comparison_to_dict(self, comparison: PeriodComparison) -> Dict[str, Any]:
        """Convert PeriodComparison to dictionary."""
        return {
            "period_type": comparison.period_type.value,
            "backup_type": comparison.backup_type,
            "current_period_start": comparison.current_period_start.isoformat(),
            "current_period_end": comparison.current_period_end.isoformat(),
            "previous_period_start": comparison.previous_period_start.isoformat(),
            "previous_period_end": comparison.previous_period_end.isoformat(),
            "has_previous_data": comparison.has_previous_data,
            "deltas": {
                metric_name: {
                    "current_value": delta.current_value,
                    "previous_value": delta.previous_value,
                    "absolute_delta": delta.absolute_delta,
                    "percentage_delta": delta.percentage_delta,
                    "is_increase": delta.is_increase,
                    "is_decrease": delta.is_decrease,
                }
                for metric_name, delta in comparison.all_deltas.items()
            },
        }
    
    def _anomaly_result_to_dict(self, result: AnomalyDetectionResult) -> Dict[str, Any]:
        """Convert AnomalyDetectionResult to dictionary."""
        return {
            "has_anomaly": result.has_anomaly,
            "anomaly_count": result.anomaly_count,
            "critical_anomalies": len(result.critical_anomalies),
            "period_start": result.metrics.period_start.isoformat(),
            "period_end": result.metrics.period_end.isoformat(),
            "backup_type": result.metrics.backup_type,
            "anomalies": [
                {
                    "anomaly_type": anomaly.anomaly_type.value,
                    "severity": anomaly.severity.value,
                    "metric_name": anomaly.metric_name,
                    "current_value": anomaly.current_value,
                    "expected_value": anomaly.expected_value,
                    "deviation_percentage": anomaly.deviation_percentage,
                }
                for anomaly in result.anomalies
            ],
        }
    
    def _calculate_summary(self, metrics: List[AggregatedMetrics]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not metrics:
            return {}
        
        total_backups = sum(m.total_count for m in metrics)
        total_success = sum(m.success_count for m in metrics)
        total_failure = sum(m.failure_count for m in metrics)
        
        avg_durations = [m.average_duration for m in metrics if m.average_duration > 0]
        
        return {
            "total_periods": len(metrics),
            "total_backups": total_backups,
            "total_success": total_success,
            "total_failure": total_failure,
            "overall_success_rate": (total_success / total_backups * 100) if total_backups > 0 else 0,
            "average_duration": sum(avg_durations) / len(avg_durations) if avg_durations else 0,
            "backup_types": list(set(m.backup_type for m in metrics)),
        }
    
    def _generate_json_report(self, data: Dict[str, Any], report_name: str) -> Path:
        """Generate JSON report."""
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_name}_report_{timestamp}.json"
        filepath = self.output_directory / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _generate_csv_report(self, data: Dict[str, Any], report_name: str) -> Path:
        """Generate CSV report."""
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_name}_report_{timestamp}.csv"
        filepath = self.output_directory / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["Report Type", "Generated At"])
            writer.writerow([data.get("report_type", ""), data.get("generated_at", "")])
            writer.writerow([])
            
            # Write metrics
            if "metrics" in data and data["metrics"]:
                metrics = data["metrics"]
                if metrics:
                    # Write metrics header
                    writer.writerow(["Metrics"])
                    writer.writerow(list(metrics[0].keys()))
                    
                    # Write metrics rows
                    for metric in metrics:
                        writer.writerow([str(v) for v in metric.values()])
                    writer.writerow([])
            
            # Write comparisons
            if "comparisons" in data and data["comparisons"]:
                comparisons = data["comparisons"]
                writer.writerow(["Comparisons"])
                # Simplified comparison data
                for comp in comparisons:
                    writer.writerow([
                        comp["backup_type"],
                        comp["current_period_start"],
                        comp["previous_period_start"],
                        len(comp.get("deltas", {})),
                    ])
                writer.writerow([])
            
            # Write anomalies
            if "anomalies" in data and data["anomalies"]:
                anomalies = data["anomalies"]
                writer.writerow(["Anomalies"])
                writer.writerow(["Backup Type", "Period Start", "Anomaly Count", "Critical Count"])
                for anomaly in anomalies:
                    writer.writerow([
                        anomaly.get("backup_type", ""),
                        anomaly.get("period_start", ""),
                        anomaly.get("anomaly_count", 0),
                        anomaly.get("critical_anomalies", 0),
                    ])
        
        return filepath
    
    def _generate_html_report(self, data: Dict[str, Any], report_name: str) -> Path:
        """Generate HTML report."""
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_name}_report_{timestamp}.html"
        filepath = self.output_directory / filename
        
        html_content = self._build_html_content(data, report_name)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _build_html_content(self, data: Dict[str, Any], report_name: str) -> str:
        """Build HTML content for report."""
        report_type = data.get("report_type", report_name)
        generated_at = data.get("generated_at", "")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backup Monitoring Report - {report_type.title()}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .summary {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .anomaly-critical {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .anomaly-high {{
            color: #f57c00;
        }}
        .anomaly-medium {{
            color: #fbc02d;
        }}
        .anomaly-low {{
            color: #388e3c;
        }}
        .delta-positive {{
            color: #d32f2f;
        }}
        .delta-negative {{
            color: #388e3c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Backup Monitoring Report</h1>
        <p><strong>Report Type:</strong> {report_type.title()}</p>
        <p><strong>Generated At:</strong> {generated_at}</p>
"""
        
        # Add summary
        if "summary" in data:
            summary = data["summary"]
            html += f"""
        <div class="summary">
            <h2>Summary</h2>
            <ul>
                <li><strong>Total Periods:</strong> {summary.get('total_periods', 0)}</li>
                <li><strong>Total Backups:</strong> {summary.get('total_backups', 0)}</li>
                <li><strong>Total Success:</strong> {summary.get('total_success', 0)}</li>
                <li><strong>Total Failure:</strong> {summary.get('total_failure', 0)}</li>
                <li><strong>Overall Success Rate:</strong> {summary.get('overall_success_rate', 0):.2f}%</li>
                <li><strong>Average Duration:</strong> {summary.get('average_duration', 0):.2f} seconds</li>
                <li><strong>Backup Types:</strong> {', '.join(summary.get('backup_types', []))}</li>
            </ul>
        </div>
"""
        
        # Add metrics table
        if "metrics" in data and data["metrics"]:
            html += """
        <h2>Metrics</h2>
        <table>
            <thead>
                <tr>
                    <th>Period Start</th>
                    <th>Period End</th>
                    <th>Backup Type</th>
                    <th>Total Count</th>
                    <th>Success Count</th>
                    <th>Failure Count</th>
                    <th>Avg Duration (s)</th>
                    <th>Success Rate (%)</th>
                </tr>
            </thead>
            <tbody>
"""
            for metric in data["metrics"]:
                html += f"""
                <tr>
                    <td>{metric.get('period_start', '')}</td>
                    <td>{metric.get('period_end', '')}</td>
                    <td>{metric.get('backup_type', '')}</td>
                    <td>{metric.get('total_count', 0)}</td>
                    <td>{metric.get('success_count', 0)}</td>
                    <td>{metric.get('failure_count', 0)}</td>
                    <td>{metric.get('average_duration', 0):.2f}</td>
                    <td>{metric.get('success_rate', 0):.2f}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""
        
        # Add comparisons
        if "comparisons" in data and data["comparisons"]:
            html += """
        <h2>Period Comparisons</h2>
        <table>
            <thead>
                <tr>
                    <th>Backup Type</th>
                    <th>Current Period</th>
                    <th>Previous Period</th>
                    <th>Changes Detected</th>
                </tr>
            </thead>
            <tbody>
"""
            for comp in data["comparisons"]:
                changes = len(comp.get("deltas", {}))
                html += f"""
                <tr>
                    <td>{comp.get('backup_type', '')}</td>
                    <td>{comp.get('current_period_start', '')} to {comp.get('current_period_end', '')}</td>
                    <td>{comp.get('previous_period_start', '')} to {comp.get('previous_period_end', '')}</td>
                    <td>{changes}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""
        
        # Add anomalies
        if "anomalies" in data and data["anomalies"]:
            html += """
        <h2>Anomalies</h2>
        <table>
            <thead>
                <tr>
                    <th>Backup Type</th>
                    <th>Period</th>
                    <th>Anomaly Count</th>
                    <th>Critical</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
            for anomaly in data["anomalies"]:
                if anomaly.get("has_anomaly"):
                    critical_count = anomaly.get("critical_anomalies", 0)
                    html += f"""
                <tr>
                    <td>{anomaly.get('backup_type', '')}</td>
                    <td>{anomaly.get('period_start', '')} to {anomaly.get('period_end', '')}</td>
                    <td>{anomaly.get('anomaly_count', 0)}</td>
                    <td class="anomaly-critical">{critical_count}</td>
                    <td>
"""
                    for a in anomaly.get("anomalies", []):
                        severity_class = f"anomaly-{a.get('severity', 'low')}"
                        html += f"""
                        <span class="{severity_class}">
                            {a.get('metric_name', '')}: {a.get('deviation_percentage', 0):.2f}% ({a.get('severity', '')})
                        </span><br>
"""
                    html += """
                    </td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html
