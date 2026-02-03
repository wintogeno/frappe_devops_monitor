import frappe
import psutil
import os
import json
from frappe.utils import now_datetime, get_datetime
from datetime import datetime, timedelta

@frappe.whitelist()
def get_system_metrics():
    """Get current system metrics"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Load average
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        
        # Process count
        process_count = len(psutil.pids())
        
        return {
            "success": True,
            "timestamp": now_datetime().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else 0,
                "load_average": {
                    "1min": round(load_avg[0], 2),
                    "5min": round(load_avg[1], 2),
                    "15min": round(load_avg[2], 2)
                }
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2)
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": round((disk.used / disk.total) * 100, 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2)
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout,
                "sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "recv_mb": round(net_io.bytes_recv / (1024**2), 2)
            },
            "processes": {
                "total": process_count
            }
        }
    except Exception as e:
        frappe.log_error(f"Error getting system metrics: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_logs(log_type="frappe", lines=100, search=None, level=None):
    """Get logs from various sources"""
    try:
        settings = frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
        
        log_files = {
            "frappe": [
                os.path.join(settings.frappe_log_path, "frappe.log"),
                os.path.join(settings.frappe_log_path, "web.log"),
                os.path.join(settings.frappe_log_path, "worker.log")
            ],
            "error": [
                os.path.join(settings.frappe_log_path, "error.log"),
                os.path.join(settings.frappe_log_path, "web.error.log")
            ],
            "scheduler": [
                os.path.join(settings.frappe_log_path, "scheduler.log")
            ],
            "nginx_access": [
                os.path.join(settings.nginx_log_path, "access.log")
            ],
            "nginx_error": [
                os.path.join(settings.nginx_log_path, "error.log")
            ],
            "supervisor": [
                os.path.join(settings.supervisor_log_path, "supervisord.log")
            ],
            "system": [
                os.path.join(settings.system_log_path, "syslog"),
                os.path.join(settings.system_log_path, "messages")
            ]
        }
        
        files = log_files.get(log_type, [])
        all_logs = []
        
        for log_file in files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read last N lines
                        f.seek(0, 2)
                        file_size = f.tell()
                        
                        # Estimate bytes to read (rough estimate: 200 chars per line)
                        bytes_to_read = min(lines * 200, file_size)
                        f.seek(max(0, file_size - bytes_to_read))
                        
                        content = f.read()
                        log_lines = content.split('\n')
                        
                        # Process each line
                        for line in log_lines[-lines:]:
                            if line.strip():
                                # Apply search filter
                                if search and search.lower() not in line.lower():
                                    continue
                                
                                # Detect log level
                                detected_level = detect_log_level(line)
                                if level and detected_level != level:
                                    continue
                                
                                all_logs.append({
                                    "source": os.path.basename(log_file),
                                    "message": line,
                                    "level": detected_level,
                                    "timestamp": extract_timestamp(line) or now_datetime().isoformat()
                                })
                except Exception as e:
                    all_logs.append({
                        "source": os.path.basename(log_file),
                        "message": f"Error reading file: {str(e)}",
                        "level": "ERROR",
                        "timestamp": now_datetime().isoformat()
                    })
        
        # Sort by timestamp (most recent first)
        all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "success": True,
            "log_type": log_type,
            "logs": all_logs[:lines]
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting logs: {str(e)}")
        return {"success": False, "error": str(e)}

def detect_log_level(line):
    """Detect log level from log line"""
    line_upper = line.upper()
    if 'CRITICAL' in line_upper or 'FATAL' in line_upper:
        return 'CRITICAL'
    elif 'ERROR' in line_upper:
        return 'ERROR'
    elif 'WARNING' in line_upper or 'WARN' in line_upper:
        return 'WARNING'
    elif 'INFO' in line_upper:
        return 'INFO'
    elif 'DEBUG' in line_upper:
        return 'DEBUG'
    return 'INFO'

def extract_timestamp(line):
    """Extract timestamp from log line if present"""
    import re
    # Common timestamp patterns
    patterns = [
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        r'(\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2})',
        r'(\w+\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(1)
    return None

@frappe.whitelist()
def get_database_stats():
    """Get database statistics"""
    try:
        # Get connection info
        db_host = frappe.conf.db_host or 'localhost'
        db_name = frappe.conf.db_name
        
        # Get process list
        processes = frappe.db.sql("""
            SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO
            FROM information_schema.PROCESSLIST
            WHERE DB = %s
            ORDER BY TIME DESC
        """, (db_name,), as_dict=True)
        
        # Get table statistics
        table_stats = frappe.db.sql("""
            SELECT 
                TABLE_NAME,
                TABLE_ROWS,
                DATA_LENGTH,
                INDEX_LENGTH,
                (DATA_LENGTH + INDEX_LENGTH) as TOTAL_SIZE
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            ORDER BY TOTAL_SIZE DESC
            LIMIT 20
        """, (db_name,), as_dict=True)
        
        # Convert bytes to MB
        for table in table_stats:
            table['DATA_SIZE_MB'] = round(table['DATA_LENGTH'] / (1024**2), 2)
            table['INDEX_SIZE_MB'] = round(table['INDEX_LENGTH'] / (1024**2), 2)
            table['TOTAL_SIZE_MB'] = round(table['TOTAL_SIZE'] / (1024**2), 2)
        
        # Get query cache status
        cache_status = frappe.db.sql("SHOW VARIABLES LIKE 'query_cache%'")
        
        # Get InnoDB status
        try:
            innodb_status = frappe.db.sql("SHOW ENGINE INNODB STATUS", as_dict=True)
        except:
            innodb_status = []
        
        return {
            "success": True,
            "connections": {
                "active": len([p for p in processes if p.COMMAND != 'Sleep']),
                "sleeping": len([p for p in processes if p.COMMAND == 'Sleep']),
                "total": len(processes)
            },
            "processes": processes[:20],
            "tables": table_stats,
            "cache_status": cache_status,
            "innodb_status": innodb_status
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting database stats: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_slow_queries():
    """Get slow query log"""
    try:
        # This would require slow query log to be enabled
        # For now, return active long-running queries
        db_name = frappe.conf.db_name
        
        slow_queries = frappe.db.sql("""
            SELECT ID, USER, HOST, TIME, STATE, INFO
            FROM information_schema.PROCESSLIST
            WHERE DB = %s AND TIME > 10
            ORDER BY TIME DESC
        """, (db_name,), as_dict=True)
        
        return {
            "success": True,
            "slow_queries": slow_queries
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting slow queries: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_frappe_info():
    """Get Frappe framework information"""
    try:
        import frappe
        
        # Get installed apps
        apps = frappe.get_installed_apps()
        
        # Get site info
        site_info = {
            "site": frappe.local.site,
            "version": frappe.__version__,
            "apps": []
        }
        
        for app in apps:
            try:
                app_module = frappe.get_module(app)
                version = getattr(app_module, '__version__', 'Unknown')
                site_info["apps"].append({
                    "name": app,
                    "version": version
                })
            except:
                site_info["apps"].append({
                    "name": app,
                    "version": "Unknown"
                })
        
        # Get scheduler status
        scheduler_status = frappe.utils.scheduler.get_scheduler_status()
        
        # Get background jobs status
        try:
            from frappe.utils.background_jobs import get_queue_list
            queues = get_queue_list()
        except:
            queues = []
        
        return {
            "success": True,
            "site_info": site_info,
            "scheduler": scheduler_status,
            "queues": queues
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting Frappe info: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def execute_command(command):
    """Execute a system command (restricted)"""
    try:
        # Only allow safe commands
        allowed_commands = ['ping', 'curl', 'netstat', 'ss', 'df', 'du', 'ps', 'top', 'htop']
        
        cmd_parts = command.split()
        if cmd_parts[0] not in allowed_commands:
            return {
                "success": False,
                "error": f"Command '{cmd_parts[0]}' is not allowed"
            }
        
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_dashboard_data():
    """Get all data needed for dashboard"""
    return {
        "system_metrics": get_system_metrics(),
        "database_stats": get_database_stats(),
        "frappe_info": get_frappe_info(),
        "recent_logs": get_logs(log_type="frappe", lines=50),
        "recent_errors": get_logs(log_type="error", lines=20)
    }
