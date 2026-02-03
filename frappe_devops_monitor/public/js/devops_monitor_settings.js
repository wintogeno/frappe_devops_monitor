frappe.ui.form.on('DevOps Monitor Settings', {
    refresh: function(frm) {
        // Add test connection button
        frm.add_custom_button(__('Test Log Paths'), function() {
            frm.call('test_log_paths').then(r => {
                if (r.message) {
                    let message = '<ul>';
                    for (let [path, result] of Object.entries(r.message)) {
                        let icon = result.valid ? '✅' : '❌';
                        message += `<li>${icon} <strong>${path}</strong>: ${result.valid ? 'Valid' : result.error}</li>`;
                    }
                    message += '</ul>';
                    frappe.msgprint(message, __('Log Path Validation'));
                }
            });
        });

        // Add view dashboard button
        frm.add_custom_button(__('View Dashboard'), function() {
            frappe.set_route('devops-monitor');
        }, __('Actions'));
    },

    validate: function(frm) {
        // Validate thresholds
        if (frm.doc.cpu_threshold < 0 || frm.doc.cpu_threshold > 100) {
            frappe.throw(__('CPU Threshold must be between 0 and 100'));
        }
        if (frm.doc.memory_threshold < 0 || frm.doc.memory_threshold > 100) {
            frappe.throw(__('Memory Threshold must be between 0 and 100'));
        }
        if (frm.doc.disk_threshold < 0 || frm.doc.disk_threshold > 100) {
            frappe.throw(__('Disk Threshold must be between 0 and 100'));
        }
    }
});
