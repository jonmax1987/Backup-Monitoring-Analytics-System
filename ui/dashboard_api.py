"""Simple API server for dashboard (Phase 1 - Basic Implementation).

This provides a minimal API endpoint that uses the Integration Layer
to serve data to the dashboard UI.
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from backup_monitoring.integration.mocks import MockUIAdapter
from backup_monitoring.integration.data_provider import IntegrationDataProvider, StandardUIAdapter


class DashboardAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard API."""
    
    def __init__(self, ui_adapter, *args, **kwargs):
        """Initialize with UI adapter."""
        self.ui_adapter = ui_adapter
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/dashboard':
            self.handle_dashboard_api(parsed_path.query)
        elif path == '/' or path == '/dashboard.html':
            self.serve_dashboard_html()
        else:
            self.send_error(404, "Not Found")
    
    def handle_dashboard_api(self, query_string: str):
        """Handle dashboard API requests."""
        try:
            # Parse query parameters
            params = parse_qs(query_string)
            start_date = params.get('start_date', [None])[0]
            end_date = params.get('end_date', [None])[0]
            backup_type = params.get('backup_type', [None])[0]
            
            # Get summary
            summary = self.ui_adapter.get_dashboard_summary()
            
            # Get filtered metrics
            daily_metrics = self.ui_adapter.get_daily_metrics(
                start_date=start_date,
                end_date=end_date,
                backup_type=backup_type
            )
            
            # Get filtered anomalies
            anomalies = self.ui_adapter.get_anomalies(
                start_date=start_date,
                end_date=end_date,
                backup_type=backup_type
            )
            
            # Convert to dictionaries
            response_data = {
                "summary": summary,
                "metrics": [self._metric_to_dict(m) for m in daily_metrics],
                "anomalies": [self._anomaly_result_to_dict(a) for a in anomalies],
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def serve_dashboard_html(self):
        """Serve the dashboard HTML file."""
        dashboard_path = Path(__file__).parent / "dashboard.html"
        
        if not dashboard_path.exists():
            self.send_error(404, "Dashboard HTML not found")
            return
        
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def send_json_response(self, data: Dict[str, Any]):
        """Send JSON response."""
        json_data = json.dumps(data, default=str)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def _metric_to_dict(self, metric):
        """Convert metric to dictionary."""
        return {
            "date": metric.date.isoformat() if hasattr(metric, 'date') else metric.period_start.isoformat(),
            "period_start": metric.period_start.isoformat(),
            "period_end": metric.period_end.isoformat(),
            "backup_type": metric.backup_type,
            "total_count": metric.total_count,
            "success_count": metric.success_count,
            "failure_count": metric.failure_count,
            "average_duration": metric.average_duration,
            "success_rate": metric.success_rate,
        }
    
    def _anomaly_result_to_dict(self, result):
        """Convert anomaly result to dictionary."""
        return {
            "has_anomaly": result.has_anomaly,
            "anomaly_count": result.anomaly_count,
            "critical_anomalies": len(result.critical_anomalies),
            "period_start": result.metrics.period_start.isoformat(),
            "period_end": result.metrics.period_end.isoformat(),
            "backup_type": result.metrics.backup_type,
            "anomalies": [
                {
                    "metric_name": a.metric_name,
                    "severity": a.severity.value,
                    "deviation_percentage": a.deviation_percentage,
                }
                for a in result.anomalies
            ],
        }
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        pass


def create_api_server(ui_adapter, port: int = 8080):
    """Create and return API server instance."""
    def handler(*args, **kwargs):
        return DashboardAPIHandler(ui_adapter, *args, **kwargs)
    
    server = HTTPServer(('localhost', port), handler)
    return server


def run_dashboard_server(port: int = 8080, use_mock: bool = True):
    """
    Run the dashboard API server.
    
    Args:
        port: Port to run server on
        use_mock: Whether to use mock data (True) or real data provider (False)
    """
    if use_mock:
        ui_adapter = MockUIAdapter()
    else:
        # In production, initialize with real data provider
        # data_provider = IntegrationDataProvider(...)
        # ui_adapter = StandardUIAdapter(data_provider)
        ui_adapter = MockUIAdapter()  # Fallback to mock for now
    
    server = create_api_server(ui_adapter, port)
    
    print(f"Dashboard server running on http://localhost:{port}")
    print(f"Open http://localhost:{port}/dashboard.html in your browser")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    import sys
    
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    run_dashboard_server(port)
