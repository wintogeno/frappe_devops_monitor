import frappe
from frappe.model.document import Document

class DevOpsMonitorSettings(Document):
    def validate(self):
        if self.cpu_threshold < 0 or self.cpu_threshold > 100:
            frappe.throw("CPU Threshold must be between 0 and 100")
        if self.memory_threshold < 0 or self.memory_threshold > 100:
            frappe.throw("Memory Threshold must be between 0 and 100")
        if self.disk_threshold < 0 or self.disk_threshold > 100:
            frappe.throw("Disk Threshold must be between 0 and 100")

    def on_update(self):
        # Clear cache when settings are updated
        frappe.cache().delete_key("devops_monitor_settings")

@frappe.whitelist()
def get_settings():
    """Get monitor settings with caching"""
    settings = frappe.cache().get_value("devops_monitor_settings")
    if not settings:
        doc = frappe.get_doc("DevOps Monitor Settings", {"site_name": frappe.local.site})
        if doc:
            settings = {
                "enable_monitoring": doc.enable_monitoring,
                "frappe_log_path": doc.frappe_log_path,
                "nginx_log_path": doc.nginx_log_path,
                "supervisor_log_path": doc.supervisor_log_path,
                "system_log_path": doc.system_log_path,
                "max_log_lines": doc.max_log_lines,
                "log_retention_days": doc.log_retention_days,
                "enable_alerts": doc.enable_alerts,
                "cpu_threshold": doc.cpu_threshold,
                "memory_threshold": doc.memory_threshold,
                "disk_threshold": doc.disk_threshold,
                "error_rate_threshold": doc.error_rate_threshold,
                "slow_query_threshold": doc.slow_query_threshold
            }
            frappe.cache().set_value("devops_monitor_settings", settings)
    return settings or {}
