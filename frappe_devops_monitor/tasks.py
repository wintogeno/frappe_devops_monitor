import frappe
from frappe.utils import now_datetime

def collect_metrics():
    """Scheduled task to collect metrics"""
    try:
        from frappe_devops_monitor.monitor import collect_all_metrics
        collect_all_metrics()
    except Exception as e:
        frappe.log_error(f"Error in collect_metrics task: {str(e)}")

def check_alerts():
    """Scheduled task to check alerts"""
    try:
        from frappe_devops_monitor.monitor import check_alerts
        check_alerts()
    except Exception as e:
        frappe.log_error(f"Error in check_alerts task: {str(e)}")

def cleanup_old_logs():
    """Scheduled task to cleanup old logs"""
    try:
        from frappe_devops_monitor.doctype.devops_log_entry.devops_log_entry import clear_old_logs
        
        settings = frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
        if settings:
            deleted_count = clear_old_logs(settings.log_retention_days)
            frappe.logger().info(f"Cleaned up {deleted_count} old log entries")
    except Exception as e:
        frappe.log_error(f"Error in cleanup_old_logs task: {str(e)}")
