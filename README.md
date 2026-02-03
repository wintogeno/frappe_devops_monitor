# Frappe DevOps Monitor

A comprehensive DevOps monitoring application for Frappe Framework that provides real-time visibility into system logs, errors, database queries, and performance metrics.

## Features

### Log Monitoring
- **Frappe Logs**: Application logs, error logs, scheduler logs
- **Nginx Logs**: Access logs and error logs with filtering
- **Supervisor Logs**: Process management logs
- **System Logs**: Syslog, auth logs, custom log files

### Database Monitoring
- **Query Monitor**: Slow query detection and analysis
- **Connection Tracking**: Active connections and pool status
- **Performance Metrics**: Query execution times, throughput

### System Metrics
- **CPU Usage**: Real-time CPU utilization
- **Memory Usage**: RAM consumption tracking
- **Disk Usage**: Storage monitoring
- **Network I/O**: Traffic statistics

### Error Tracking
- **Error Aggregation**: Group similar errors
- **Stack Trace Analysis**: Detailed error information
- **Alert System**: Configurable notifications

## Installation

```bash
# Get the app
bench get-app frappe_devops_monitor /path/to/frappe_devops_monitor

# Install on site
bench --site your-site.local install-app frappe_devops_monitor

# Setup monitoring
bench --site your-site.local execute frappe_devops_monitor.setup.setup_monitoring
```

## Configuration

### Log Paths
Configure log file paths in **DevOps Monitor Settings**:
- Frappe Log Path: `/home/frappe/frappe-bench/logs`
- Nginx Log Path: `/var/log/nginx`
- Supervisor Log Path: `/var/log/supervisor`

### Alert Rules
Set up alert thresholds:
- CPU Usage > 80%
- Memory Usage > 85%
- Disk Usage > 90%
- Error Rate > 10/min

## Usage

### Dashboard
Access the monitoring dashboard at:
```
https://your-site.local/app/devops-monitor
```

### API Endpoints

#### Get System Metrics
```
GET /api/method/frappe_devops_monitor.api.get_system_metrics
```

#### Get Logs
```
GET /api/method/frappe_devops_monitor.api.get_logs?log_type=frappe&lines=100
```

#### Get Database Stats
```
GET /api/method/frappe_devops_monitor.api.get_database_stats
```

## Architecture

```
frappe_devops_monitor/
├── frappe_devops_monitor/
│   ├── doctype/           # Frappe DocTypes
│   ├── api.py            # REST API endpoints
│   ├── log_collector.py  # Log collection logic
│   ├── monitor.py        # System monitoring
│   └── utils.py          # Utility functions
├── dashboard/            # React Dashboard
│   ├── src/
│   └── build/
└── hooks.py             # Frappe hooks
```

## License

MIT License
