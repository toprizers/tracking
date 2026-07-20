let socket = null;

function initSocket() {
    socket = io();

    socket.on('connect', function() {
        console.log('Connected to server');
    });

    socket.on('new_alert', function(data) {
        showNotification(data);
        updateAlertCount();
    });

    socket.on('new_screenshot', function(data) {
        showNotification({
            type: 'screenshot',
            employee_name: data.employee_name,
            message: 'New screenshot uploaded',
            severity: 'info'
        });
    });

    socket.on('agent_heartbeat', function(data) {
        updateEmployeeStatus(data.employee_id, 'active');
    });
}

function showNotification(data) {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const severityColors = {
        'critical': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info',
        'screenshot': 'bg-success'
    };

    const color = severityColors[data.severity] || 'bg-info';

    const toast = document.createElement('div');
    toast.className = `toast-notification alert ${color} text-white alert-dismissible fade show mb-2`;
    toast.innerHTML = `
        <strong>${data.employee_name}</strong>
        <p class="mb-0 small">${data.message}</p>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function updateAlertCount() {
    fetch('/api/dashboard-data')
        .then(r => r.json())
        .then(data => {
            const badge = document.getElementById('alert-count');
            if (badge) {
                if (data.alerts > 0) {
                    badge.textContent = data.alerts;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        });
}

function updateEmployeeStatus(empId, status) {
    const row = document.querySelector(`[data-employee-id="${empId}"]`);
    if (row) {
        const badge = row.querySelector('.badge');
        if (badge) {
            badge.className = 'badge bg-success';
            badge.textContent = 'Active';
        }
    }
}

function markAllRead() {
    fetch('/api/alerts/read-all', { method: 'POST' })
        .then(() => location.reload());
}

document.addEventListener('DOMContentLoaded', function() {
    initSocket();
    updateAlertCount();
    setInterval(updateAlertCount, 30000);
});
