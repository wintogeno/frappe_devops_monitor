import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class DevOpsLogEntry(Document):
    def before_insert(self):
        if not self.timestamp:
            self.timestamp = now_datetime()

@frappe.whitelist()
def get_recent_logs(log_type=None, log_level=None, limit=100):
    """Get recent log entries with optional filtering"""
    filters = {}
    if log_type:
        filters["log_type"] = log_type
    if log_level:
        filters["log_level"] = log_level
    
    logs = frappe.get_all(
        "DevOps Log Entry",
        filters=filters,
        fields=["name", "timestamp", "log_type", "log_level", "source", "message"],
        order_by="timestamp desc",
        limit=limit
    )
    return logs

@frappe.whitelist()
def clear_old_logs(days=30):
    """Clear log entries older than specified days"""
    from frappe.utils import add_days
    cutoff_date = add_days(now_datetime(), -days)
    
    old_logs = frappe.get_all(
        "DevOps Log Entry",
        filters={"timestamp": ["<", cutoff_date]},
        pluck="name"
    )
    
    for log_name in old_logs:
        frappe.delete_doc("DevOps Log Entry", log_name, ignore_permissions=True)
    
    frappe.db.commit()
    return len(old_logs)
