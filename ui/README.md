# Dashboard UI

Basic dashboard for visualizing backup monitoring data.

## Features

- **Summary Statistics**: Total backups, success rate, failures, anomalies
- **Metrics Table**: Daily metrics with filtering
- **Anomalies Table**: Detected anomalies with severity levels
- **Filtering**: Filter by date range, backup type, and status
- **Integration Layer**: Consumes data only through the Integration Layer

## Running the Dashboard

### Option 1: Using the API Server (Recommended)

```bash
# Run the API server
python ui/dashboard_api.py

# Open http://localhost:8080/dashboard.html in your browser
```

### Option 2: Static HTML (Mock Data)

Simply open `dashboard.html` in your browser. It will use mock data if the API is not available.

## API Endpoints

The dashboard API server provides:

- `GET /dashboard.html` - Serves the dashboard HTML
- `GET /api/dashboard` - Returns dashboard data in JSON format

### Query Parameters

- `start_date` - Filter metrics from this date (YYYY-MM-DD)
- `end_date` - Filter metrics until this date (YYYY-MM-DD)
- `backup_type` - Filter by backup type

## Architecture

The dashboard follows the architectural principle that **UI must consume data only via the Integration Layer** (ADR-001).

- Dashboard HTML/JavaScript makes API calls
- API server uses `UIAdapter` from Integration Layer
- No direct coupling to core logic

## Future Enhancements

- Charts/graphs for duration trends
- Real-time updates
- Export functionality
- More detailed visualizations
