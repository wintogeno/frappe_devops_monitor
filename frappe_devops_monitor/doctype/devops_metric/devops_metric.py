import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class DevOpsMetric(Document):
    def before_insert(self):
        if not self.timestamp:
            self.timestamp = now_datetime()

@frappe.whitelist()
def get_metrics_history(metric_type=None, metric_name=None, hours=24):
    """Get metrics history for specified time range"""
    from frappe.utils import add_to_date
    
    cutoff_time = add_to_date(now_datetime(), hours=-hours)
    filters = {"timestamp": [">=", cutoff_time]}
    
    if metric_type:
        filters["metric_type"] = metric_type
    if metric_name:
        filters["metric_name"] = metric_name
    
    metrics = frappe.get_all(
        "DevOps Metric",
        filters=filters,
        fields=["timestamp", "metric_type", "metric_name", "value", "unit"],
        order_by="timestamp asc"
    )
    return metrics

@frappe.whitelist()
def get_latest_metrics():
    """Get latest values for all metric types"""
    latest = {}
    
    for metric_type in ["System", "Database", "Application", "Network"]:
        metrics = frappe.get_all(
            "DevOps Metric",
            filters={"metric_type": metric_type},
            fields=["metric_name", "value", "unit", "timestamp"],
            order_by="timestamp desc",
            limit_page_length=20
        )
        
        # Get unique latest metrics
        seen = set()
        latest[metric_type] = []
        for m in metrics:
            if m.metric_name not in seen:
                seen.add(m.metric_name)
                latest[metric_type].append(m)
    
    return latest
