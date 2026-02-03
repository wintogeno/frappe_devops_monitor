import frappe
from frappe import _

def get_context(context):
    context.no_header = True
    context.no_sidebar = True
    context.show_toolbar = False
    context.title = _('DevOps Monitor')
    
    # Add CSRF token for API calls
    context.csrf_token = frappe.sessions.get_csrf_token()
    
    return context
