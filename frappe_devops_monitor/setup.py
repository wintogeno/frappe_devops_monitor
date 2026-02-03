import frappe
from frappe import _

def after_install():
    """Setup after app installation"""
    try:
        # Create default settings
        create_default_settings()
        
        # Create custom roles
        create_roles()
        
        # Setup workspace
        setup_workspace()
        
        frappe.msgprint(_("Frappe DevOps Monitor has been installed successfully. Please configure the settings."))
        
    except Exception as e:
        frappe.log_error(f"Error in after_install: {str(e)}")
        frappe.msgprint(_("Error setting up DevOps Monitor. Please check error logs."))

def before_uninstall():
    """Cleanup before app uninstallation"""
    try:
        # Delete custom roles
        delete_roles()
        
        # Clear scheduled jobs
        clear_scheduled_jobs()
        
    except Exception as e:
        frappe.log_error(f"Error in before_uninstall: {str(e)}")

def create_default_settings():
    """Create default monitor settings for current site"""
    try:
        if not frappe.db.exists("DevOps Monitor Settings", {"site_name": frappe.local.site}):
            doc = frappe.new_doc("DevOps Monitor Settings")
            doc.site_name = frappe.local.site
            doc.enable_monitoring = 1
            doc.frappe_log_path = "~/frappe-bench/logs"
            doc.nginx_log_path = "/var/log/nginx"
            doc.supervisor_log_path = "/var/log/supervisor"
            doc.system_log_path = "/var/log"
            doc.max_log_lines = 1000
            doc.log_retention_days = 30
            doc.enable_alerts = 1
            doc.cpu_threshold = 80
            doc.memory_threshold = 85
            doc.disk_threshold = 90
            doc.error_rate_threshold = 10
            doc.slow_query_threshold = 1000
            doc.insert(ignore_permissions=True)
            
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error creating default settings: {str(e)}")

def create_roles():
    """Create custom roles for DevOps Monitor"""
    roles = [
        {
            "role_name": "DevOps Admin",
            "desk_access": 1
        },
        {
            "role_name": "DevOps Viewer",
            "desk_access": 1
        }
    ]
    
    for role_data in roles:
        try:
            if not frappe.db.exists("Role", role_data["role_name"]):
                role = frappe.new_doc("Role")
                role.role_name = role_data["role_name"]
                role.desk_access = role_data["desk_access"]
                role.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error creating role {role_data['role_name']}: {str(e)}")
    
    frappe.db.commit()

def delete_roles():
    """Delete custom roles"""
    roles = ["DevOps Admin", "DevOps Viewer"]
    
    for role_name in roles:
        try:
            if frappe.db.exists("Role", role_name):
                frappe.delete_doc("Role", role_name, ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error deleting role {role_name}: {str(e)}")
    
    frappe.db.commit()

def setup_workspace():
    """Setup DevOps Monitor workspace"""
    try:
        # Create workspace
        if not frappe.db.exists("Workspace", "DevOps Monitor"):
            workspace = frappe.new_doc("Workspace")
            workspace.name = "DevOps Monitor"
            workspace.title = "DevOps Monitor"
            workspace.label = "DevOps Monitor"
            workspace.for_user = ""
            workspace.is_standard = 1
            workspace.module = "Frappe DevOps Monitor"
            workspace.content = frappe.as_json([
                {
                    "type": "header",
                    "data": "Dashboard"
                },
                {
                    "type": "shortcut",
                    "data": {
                        "name": "DevOps Dashboard",
                        "link": "/app/devops-monitor",
                        "icon": "dashboard"
                    }
                },
                {
                    "type": "header",
                    "data": "Configuration"
                },
                {
                    "type": "shortcut",
                    "data": {
                        "name": "Settings",
                        "link": "/app/devops-monitor-settings",
                        "icon": "settings"
                    }
                },
                {
                    "type": "header",
                    "data": "Logs"
                },
                {
                    "type": "shortcut",
                    "data": {
                        "name": "Log Entries",
                        "link": "/app/devops-log-entry",
                        "icon": "file-text"
                    }
                },
                {
                    "type": "shortcut",
                    "data": {
                        "name": "Metrics",
                        "link": "/app/devops-metric",
                        "icon": "activity"
                    }
                }
            ])
            workspace.insert(ignore_permissions=True)
            
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error setting up workspace: {str(e)}")

def clear_scheduled_jobs():
    """Clear scheduled jobs for this app"""
    try:
        scheduled_jobs = frappe.get_all("Scheduled Job Type", {
            "method": ["like", "frappe_devops_monitor.%"]
        })
        
        for job in scheduled_jobs:
            frappe.delete_doc("Scheduled Job Type", job.name, ignore_permissions=True)
        
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error clearing scheduled jobs: {str(e)}")

@frappe.whitelist()
def setup_monitoring():
    """Manual setup of monitoring"""
    try:
        create_default_settings()
        create_roles()
        setup_workspace()
        return {"success": True, "message": "Monitoring setup completed"}
    except Exception as e:
        return {"success": False, "error": str(e)}
