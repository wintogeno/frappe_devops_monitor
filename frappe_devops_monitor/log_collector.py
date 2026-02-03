import frappe
import os
import re
from datetime import datetime
from frappe.utils import now_datetime, add_to_date

class LogCollector:
    """Collect and process logs from various sources"""
    
    def __init__(self):
        self.settings = self._get_settings()
    
    def _get_settings(self):
        """Get monitor settings"""
        try:
            return frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
        except:
            return None
    
    def collect_frappe_logs(self, lines=100):
        """Collect Frappe application logs"""
        if not self.settings:
            return []
        
        log_files = [
            ("frappe.log", os.path.join(self.settings.frappe_log_path, "frappe.log")),
            ("web.log", os.path.join(self.settings.frappe_log_path, "web.log")),
            ("worker.log", os.path.join(self.settings.frappe_log_path, "worker.log")),
            ("scheduler.log", os.path.join(self.settings.frappe_log_path, "scheduler.log"))
        ]
        
        logs = []
        for source, log_file in log_files:
            if os.path.exists(log_file):
                file_logs = self._read_log_file(log_file, lines, source)
                logs.extend(file_logs)
        
        return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:lines]
    
    def collect_error_logs(self, lines=100):
        """Collect error logs"""
        if not self.settings:
            return []
        
        log_files = [
            ("error.log", os.path.join(self.settings.frappe_log_path, "error.log")),
            ("web.error.log", os.path.join(self.settings.frappe_log_path, "web.error.log"))
        ]
        
        logs = []
        for source, log_file in log_files:
            if os.path.exists(log_file):
                file_logs = self._read_log_file(log_file, lines, source)
                logs.extend(file_logs)
        
        return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:lines]
    
    def collect_nginx_logs(self, log_type='access', lines=100):
        """Collect Nginx logs"""
        if not self.settings:
            return []
        
        log_file = os.path.join(
            self.settings.nginx_log_path,
            f"{log_type}.log"
        )
        
        if os.path.exists(log_file):
            return self._read_log_file(log_file, lines, f"nginx-{log_type}")
        return []
    
    def collect_supervisor_logs(self, lines=100):
        """Collect Supervisor logs"""
        if not self.settings:
            return []
        
        log_file = os.path.join(self.settings.supervisor_log_path, "supervisord.log")
        
        if os.path.exists(log_file):
            return self._read_log_file(log_file, lines, "supervisor")
        return []
    
    def _read_log_file(self, file_path, lines, source):
        """Read last N lines from log file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read file content
                f.seek(0, 2)
                file_size = f.tell()
                
                # Estimate bytes to read
                bytes_to_read = min(lines * 300, file_size)
                f.seek(max(0, file_size - bytes_to_read))
                
                content = f.read()
                log_lines = content.split('\n')
                
                parsed_logs = []
                for line in log_lines[-lines:]:
                    if line.strip():
                        parsed = self._parse_log_line(line, source)
                        parsed_logs.append(parsed)
                
                return parsed_logs
                
        except Exception as e:
            frappe.log_error(f"Error reading log file {file_path}: {str(e)}")
            return []
    
    def _parse_log_line(self, line, source):
        """Parse a log line and extract information"""
        # Detect log level
        level = self._detect_log_level(line)
        
        # Extract timestamp
        timestamp = self._extract_timestamp(line) or now_datetime().isoformat()
        
        # Extract message
        message = self._clean_log_message(line)
        
        return {
            "timestamp": timestamp,
            "source": source,
            "level": level,
            "message": message,
            "raw": line
        }
    
    def _detect_log_level(self, line):
        """Detect log level from line"""
        line_upper = line.upper()
        if any(x in line_upper for x in ['CRITICAL', 'FATAL', 'EMERGENCY']):
            return 'CRITICAL'
        elif 'ERROR' in line_upper:
            return 'ERROR'
        elif any(x in line_upper for x in ['WARNING', 'WARN']):
            return 'WARNING'
        elif 'INFO' in line_upper:
            return 'INFO'
        elif 'DEBUG' in line_upper:
            return 'DEBUG'
        return 'INFO'
    
    def _extract_timestamp(self, line):
        """Extract timestamp from log line"""
        patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)',
            r'(\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2})',
            r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None
    
    def _clean_log_message(self, line):
        """Clean and format log message"""
        # Remove common timestamp patterns from message
        patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s*',
            r'\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2}\s*',
            r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s*'
        ]
        
        message = line
        for pattern in patterns:
            message = re.sub(pattern, '', message)
        
        return message.strip()
    
    def save_to_db(self, logs, log_type):
        """Save logs to database"""
        for log in logs:
            try:
                doc = frappe.new_doc("DevOps Log Entry")
                doc.timestamp = log.get('timestamp', now_datetime())
                doc.log_type = log_type
                doc.log_level = log.get('level', 'INFO')
                doc.source = log.get('source', 'unknown')
                doc.message = log.get('message', '')[:4000]  # Limit message length
                doc.details = log.get('raw', '')
                doc.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(f"Error saving log entry: {str(e)}")
        
        frappe.db.commit()

def collect_all_logs():
    """Collect all logs and save to database"""
    collector = LogCollector()
    
    # Collect Frappe logs
    frappe_logs = collector.collect_frappe_logs(lines=100)
    collector.save_to_db(frappe_logs, 'Frappe')
    
    # Collect Error logs
    error_logs = collector.collect_error_logs(lines=50)
    collector.save_to_db(error_logs, 'Error')
    
    # Collect Nginx logs
    nginx_access = collector.collect_nginx_logs('access', lines=50)
    collector.save_to_db(nginx_access, 'Nginx')
    
    nginx_error = collector.collect_nginx_logs('error', lines=20)
    collector.save_to_db(nginx_error, 'Nginx')
    
    # Collect Supervisor logs
    supervisor_logs = collector.collect_supervisor_logs(lines=50)
    collector.save_to_db(supervisor_logs, 'Supervisor')

@frappe.whitelist()
def get_log_summary(hours=24):
    """Get summary of logs for specified time range"""
    from frappe.utils import add_to_date
    
    cutoff_time = add_to_date(now_datetime(), hours=-hours)
    
    # Get log counts by type
    log_counts = frappe.db.sql("""
        SELECT 
            log_type,
            log_level,
            COUNT(*) as count
        FROM `tabDevOps Log Entry`
        WHERE timestamp >= %s
        GROUP BY log_type, log_level
    """, (cutoff_time,), as_dict=True)
    
    # Get recent errors
    recent_errors = frappe.get_all(
        "DevOps Log Entry",
        filters={
            "timestamp": [">=", cutoff_time],
            "log_level": ["in", ["ERROR", "CRITICAL"]]
        },
        fields=["timestamp", "source", "message"],
        order_by="timestamp desc",
        limit=10
    )
    
    # Get top error sources
    top_sources = frappe.db.sql("""
        SELECT 
            source,
            COUNT(*) as count
        FROM `tabDevOps Log Entry`
        WHERE timestamp >= %s AND log_level IN ('ERROR', 'CRITICAL')
        GROUP BY source
        ORDER BY count DESC
        LIMIT 5
    """, (cutoff_time,), as_dict=True)
    
    return {
        "log_counts": log_counts,
        "recent_errors": recent_errors,
        "top_error_sources": top_sources
    }
