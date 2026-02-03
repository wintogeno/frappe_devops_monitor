import frappe
import os
import re
from datetime import datetime
from frappe.utils import now_datetime, format_datetime

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    if bytes_value is None:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_duration(seconds):
    """Format seconds to human readable duration"""
    if seconds is None or seconds == 0:
        return "0s"
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"

def get_log_level_color(level):
    """Get color for log level"""
    colors = {
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'orange',
        'ERROR': 'red',
        'CRITICAL': 'darkred'
    }
    return colors.get(level, 'gray')

def get_log_level_icon(level):
    """Get icon for log level"""
    icons = {
        'DEBUG': 'bug',
        'INFO': 'info',
        'WARNING': 'alert-triangle',
        'ERROR': 'x-circle',
        'CRITICAL': 'alert-octagon'
    }
    return icons.get(level, 'file-text')

def parse_nginx_log_line(line):
    """Parse Nginx access log line"""
    # Common Nginx log format
    # $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
    pattern = r'^(?P<ip>[\d.]+)\s+-\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+"(?P<request>[^"]*)"\s+(?P<status>\d+)\s+(?P<bytes>\d+)\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)"'
    
    match = re.match(pattern, line)
    if match:
        return match.groupdict()
    return None

def parse_error_log_line(line):
    """Parse error log line"""
    # Common error log format
    # [timestamp] [level] [source] message
    pattern = r'\[(?P<time>[^\]]+)\]\s+\[(?P<level>\w+)\](?:\s+\[(?P<source>[^\]]+)\])?\s+(?P<message>.+)'
    
    match = re.match(pattern, line)
    if match:
        return match.groupdict()
    return None

def tail_log_file(file_path, lines=100):
    """Tail a log file and return last N lines"""
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read file in chunks from end
            f.seek(0, 2)
            file_size = f.tell()
            
            chunk_size = 8192
            data = []
            bytes_read = 0
            
            while bytes_read < file_size and len(data) < lines:
                bytes_to_read = min(chunk_size, file_size - bytes_read)
                f.seek(-bytes_to_read, 1)
                chunk = f.read(bytes_to_read)
                bytes_read += bytes_to_read
                
                lines_in_chunk = chunk.split('\n')
                data = lines_in_chunk + data
                
                if bytes_read >= file_size:
                    break
            
            return data[-lines:]
            
    except Exception as e:
        frappe.log_error(f"Error tailing file {file_path}: {str(e)}")
        return []

def search_in_logs(log_files, search_term, max_results=100):
    """Search for term in multiple log files"""
    results = []
    
    for log_file in log_files:
        if not os.path.exists(log_file):
            continue
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if search_term.lower() in line.lower():
                        results.append({
                            "file": os.path.basename(log_file),
                            "line": line_num,
                            "content": line.strip()
                        })
                        
                        if len(results) >= max_results:
                            return results
        except Exception as e:
            frappe.log_error(f"Error searching in {log_file}: {str(e)}")
    
    return results

def get_system_info():
    """Get comprehensive system information"""
    import platform
    import psutil
    
    info = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation()
        },
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "hostname": platform.node()
    }
    
    return info

def get_disk_partitions():
    """Get disk partition information"""
    import psutil
    
    partitions = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": (usage.used / usage.total) * 100
            })
        except:
            pass
    
    return partitions

def get_network_interfaces():
    """Get network interface information"""
    import psutil
    
    interfaces = []
    stats = psutil.net_if_stats()
    addresses = psutil.net_if_addrs()
    
    for name, stat in stats.items():
        interface = {
            "name": name,
            "is_up": stat.isup,
            "speed": stat.speed,
            "mtu": stat.mtu,
            "addresses": []
        }
        
        if name in addresses:
            for addr in addresses[name]:
                interface["addresses"].append({
                    "family": addr.family.name if hasattr(addr.family, 'name') else str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
        
        interfaces.append(interface)
    
    return interfaces

def validate_log_path(path):
    """Validate if log path exists and is readable"""
    if not path:
        return {"valid": False, "error": "Path is empty"}
    
    # Expand user home directory
    path = os.path.expanduser(path)
    
    if not os.path.exists(path):
        return {"valid": False, "error": f"Path does not exist: {path}"}
    
    if not os.path.isdir(path):
        return {"valid": False, "error": f"Path is not a directory: {path}"}
    
    if not os.access(path, os.R_OK):
        return {"valid": False, "error": f"Path is not readable: {path}"}
    
    return {"valid": True, "path": path}

def get_log_files_in_path(path, extensions=None):
    """Get all log files in a directory"""
    if not extensions:
        extensions = ['.log']
    
    path = os.path.expanduser(path)
    
    if not os.path.exists(path):
        return []
    
    log_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                log_files.append({
                    "name": file,
                    "path": os.path.join(root, file),
                    "size": os.path.getsize(os.path.join(root, file))
                })
    
    return log_files
