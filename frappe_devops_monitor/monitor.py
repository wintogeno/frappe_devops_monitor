import frappe
import psutil
import os
from datetime import datetime
from frappe.utils import now_datetime, add_to_date

class SystemMonitor:
    """Monitor system metrics and store in database"""
    
    def __init__(self):
        self.settings = self._get_settings()
    
    def _get_settings(self):
        """Get monitor settings"""
        try:
            return frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
        except:
            return None
    
    def collect_metrics(self):
        """Collect all system metrics"""
        if not self.settings or not self.settings.enable_monitoring:
            return
        
        try:
            # Collect CPU metrics
            self._collect_cpu_metrics()
            
            # Collect Memory metrics
            self._collect_memory_metrics()
            
            # Collect Disk metrics
            self._collect_disk_metrics()
            
            # Collect Network metrics
            self._collect_network_metrics()
            
            # Collect Process metrics
            self._collect_process_metrics()
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error collecting metrics: {str(e)}")
    
    def _collect_cpu_metrics(self):
        """Collect CPU metrics"""
        try:
            # CPU percent
            cpu_percent = psutil.cpu_percent(interval=1)
            self._save_metric("System", "cpu_percent", cpu_percent, "%")
            
            # CPU count
            cpu_count = psutil.cpu_count()
            self._save_metric("System", "cpu_count", cpu_count, "cores")
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                self._save_metric("System", "cpu_frequency", cpu_freq.current, "MHz")
            
            # Load average
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                self._save_metric("System", "load_avg_1min", load_avg[0], "")
                self._save_metric("System", "load_avg_5min", load_avg[1], "")
                self._save_metric("System", "load_avg_15min", load_avg[2], "")
            
            # Per-CPU usage
            per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
            for i, usage in enumerate(per_cpu):
                self._save_metric("System", f"cpu_{i}_usage", usage, "%")
                
        except Exception as e:
            frappe.log_error(f"Error collecting CPU metrics: {str(e)}")
    
    def _collect_memory_metrics(self):
        """Collect memory metrics"""
        try:
            memory = psutil.virtual_memory()
            
            self._save_metric("System", "memory_percent", memory.percent, "%")
            self._save_metric("System", "memory_used_gb", memory.used / (1024**3), "GB")
            self._save_metric("System", "memory_available_gb", memory.available / (1024**3), "GB")
            self._save_metric("System", "memory_total_gb", memory.total / (1024**3), "GB")
            
            # Swap memory
            swap = psutil.swap_memory()
            self._save_metric("System", "swap_percent", swap.percent, "%")
            self._save_metric("System", "swap_used_gb", swap.used / (1024**3), "GB")
            
        except Exception as e:
            frappe.log_error(f"Error collecting memory metrics: {str(e)}")
    
    def _collect_disk_metrics(self):
        """Collect disk metrics"""
        try:
            disk = psutil.disk_usage('/')
            
            disk_percent = (disk.used / disk.total) * 100
            self._save_metric("System", "disk_percent", disk_percent, "%")
            self._save_metric("System", "disk_used_gb", disk.used / (1024**3), "GB")
            self._save_metric("System", "disk_free_gb", disk.free / (1024**3), "GB")
            self._save_metric("System", "disk_total_gb", disk.total / (1024**3), "GB")
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self._save_metric("System", "disk_read_mb", disk_io.read_bytes / (1024**2), "MB")
                self._save_metric("System", "disk_write_mb", disk_io.write_bytes / (1024**2), "MB")
            
        except Exception as e:
            frappe.log_error(f"Error collecting disk metrics: {str(e)}")
    
    def _collect_network_metrics(self):
        """Collect network metrics"""
        try:
            net_io = psutil.net_io_counters()
            
            self._save_metric("Network", "net_sent_mb", net_io.bytes_sent / (1024**2), "MB")
            self._save_metric("Network", "net_recv_mb", net_io.bytes_recv / (1024**2), "MB")
            self._save_metric("Network", "net_packets_sent", net_io.packets_sent, "packets")
            self._save_metric("Network", "net_packets_recv", net_io.packets_recv, "packets")
            self._save_metric("Network", "net_errors_in", net_io.errin, "errors")
            self._save_metric("Network", "net_errors_out", net_io.errout, "errors")
            
            # Network connections
            connections = psutil.net_connections()
            self._save_metric("Network", "net_connections", len(connections), "connections")
            
        except Exception as e:
            frappe.log_error(f"Error collecting network metrics: {str(e)}")
    
    def _collect_process_metrics(self):
        """Collect process metrics"""
        try:
            # Total processes
            process_count = len(psutil.pids())
            self._save_metric("System", "process_count", process_count, "processes")
            
            # Frappe-specific processes
            frappe_processes = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'frappe' in cmdline.lower() or 'gunicorn' in cmdline.lower():
                            frappe_processes += 1
                except:
                    pass
            
            self._save_metric("Application", "frappe_processes", frappe_processes, "processes")
            
            # Top memory-consuming processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['memory_percent']:
                        processes.append(pinfo)
                except:
                    pass
            
            processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            
            for i, proc in enumerate(processes[:5]):
                self._save_metric(
                    "System", 
                    f"top_proc_{i+1}_memory", 
                    proc.get('memory_percent', 0), 
                    "%",
                    details={"name": proc.get('name', 'unknown'), "pid": proc.get('pid', 0)}
                )
            
        except Exception as e:
            frappe.log_error(f"Error collecting process metrics: {str(e)}")
    
    def _save_metric(self, metric_type, metric_name, value, unit, details=None):
        """Save metric to database"""
        try:
            doc = frappe.new_doc("DevOps Metric")
            doc.timestamp = now_datetime()
            doc.metric_type = metric_type
            doc.metric_name = metric_name
            doc.value = value
            doc.unit = unit
            if details:
                doc.details = frappe.as_json(details)
            doc.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error saving metric {metric_name}: {str(e)}")

class DatabaseMonitor:
    """Monitor database metrics"""
    
    def __init__(self):
        self.settings = self._get_settings()
    
    def _get_settings(self):
        """Get monitor settings"""
        try:
            return frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
        except:
            return None
    
    def collect_metrics(self):
        """Collect database metrics"""
        if not self.settings or not self.settings.enable_monitoring:
            return
        
        try:
            db_name = frappe.conf.db_name
            
            # Active connections
            connections = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM information_schema.PROCESSLIST
                WHERE DB = %s
            """, (db_name,), as_dict=True)
            
            if connections:
                self._save_metric("Database", "active_connections", connections[0].count, "connections")
            
            # Table count
            table_count = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
            """, (db_name,), as_dict=True)
            
            if table_count:
                self._save_metric("Database", "table_count", table_count[0].count, "tables")
            
            # Database size
            db_size = frappe.db.sql("""
                SELECT 
                    SUM(DATA_LENGTH + INDEX_LENGTH) as size
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
            """, (db_name,), as_dict=True)
            
            if db_size and db_size[0].size:
                self._save_metric("Database", "database_size_mb", db_size[0].size / (1024**2), "MB")
            
            # Slow queries (queries running > threshold)
            slow_threshold = self.settings.slow_query_threshold or 1000
            slow_queries = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM information_schema.PROCESSLIST
                WHERE DB = %s AND TIME > %s
            """, (db_name, slow_threshold / 1000), as_dict=True)
            
            if slow_queries:
                self._save_metric("Database", "slow_queries", slow_queries[0].count, "queries")
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error collecting database metrics: {str(e)}")
    
    def _save_metric(self, metric_type, metric_name, value, unit):
        """Save metric to database"""
        try:
            doc = frappe.new_doc("DevOps Metric")
            doc.timestamp = now_datetime()
            doc.metric_type = metric_type
            doc.metric_name = metric_name
            doc.value = value
            doc.unit = unit
            doc.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error saving database metric {metric_name}: {str(e)}")

class AlertManager:
    """Manage alerts based on thresholds"""
    
    def __init__(self):
        self.settings = self._get_settings()
    
    def _get_settings(self):
        """Get monitor settings"""
        try:
            return frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
        except:
            return None
    
    def check_alerts(self):
        """Check if any metrics exceed thresholds"""
        if not self.settings or not self.settings.enable_alerts:
            return
        
        try:
            # Get latest metrics
            latest = self._get_latest_metrics()
            
            alerts = []
            
            # Check CPU threshold
            if latest.get('cpu_percent', 0) > self.settings.cpu_threshold:
                alerts.append({
                    "type": "CPU",
                    "message": f"CPU usage is {latest['cpu_percent']:.1f}%, exceeding threshold of {self.settings.cpu_threshold}%"
                })
            
            # Check Memory threshold
            if latest.get('memory_percent', 0) > self.settings.memory_threshold:
                alerts.append({
                    "type": "Memory",
                    "message": f"Memory usage is {latest['memory_percent']:.1f}%, exceeding threshold of {self.settings.memory_threshold}%"
                })
            
            # Check Disk threshold
            if latest.get('disk_percent', 0) > self.settings.disk_threshold:
                alerts.append({
                    "type": "Disk",
                    "message": f"Disk usage is {latest['disk_percent']:.1f}%, exceeding threshold of {self.settings.disk_threshold}%"
                })
            
            # Send alerts
            for alert in alerts:
                self._send_alert(alert)
            
        except Exception as e:
            frappe.log_error(f"Error checking alerts: {str(e)}")
    
    def _get_latest_metrics(self):
        """Get latest metric values"""
        metrics = {}
        
        try:
            result = frappe.db.sql("""
                SELECT metric_name, value
                FROM `tabDevOps Metric`
                WHERE metric_type = 'System'
                ORDER BY timestamp DESC
            """, as_dict=True)
            
            for row in result:
                if row.metric_name not in metrics:
                    metrics[row.metric_name] = row.value
            
        except Exception as e:
            frappe.log_error(f"Error getting latest metrics: {str(e)}")
        
        return metrics
    
    def _send_alert(self, alert):
        """Send alert notification"""
        try:
            # Get alert recipients
            settings = frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
            
            for recipient in settings.alert_recipients:
                if recipient.notify_on_alert:
                    # Create notification
                    notification = frappe.new_doc("Notification Log")
                    notification.for_user = recipient.user
                    notification.subject = f"DevOps Alert: {alert['type']}"
                    notification.email_content = alert['message']
                    notification.type = "Alert"
                    notification.insert(ignore_permissions=True)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error sending alert: {str(e)}")

def collect_all_metrics():
    """Collect all metrics"""
    system_monitor = SystemMonitor()
    system_monitor.collect_metrics()
    
    db_monitor = DatabaseMonitor()
    db_monitor.collect_metrics()

def check_alerts():
    """Check and send alerts"""
    alert_manager = AlertManager()
    alert_manager.check_alerts()
