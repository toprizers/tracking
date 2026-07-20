const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const { queryAll, queryOne, runSql } = require('../db');
const { requireLogin } = require('../middleware/auth');

router.get('/', requireLogin, (req, res) => {
  const employees = queryAll('SELECT * FROM employees');
  const totalAlerts = queryOne('SELECT COUNT(*) as count FROM alerts WHERE is_read = 0').count;
  const latestScreenshots = queryAll(`
    SELECT s.*, e.name as employee_name FROM screenshots s
    JOIN employees e ON s.employee_id = e.id
    ORDER BY s.captured_at DESC LIMIT 8
  `);

  const recentAlerts = queryAll(`
    SELECT a.*, e.name as employee_name FROM alerts a
    JOIN employees e ON a.employee_id = e.id
    WHERE a.is_read = 0
    ORDER BY a.created_at DESC LIMIT 10
  `);

  const activeCount = employees.filter(e => e.status === 'active').length;

  res.render('dashboard.html', {
    employees,
    total_employees: employees.length,
    active_employees: activeCount,
    total_alerts: totalAlerts,
    recent_alerts: recentAlerts,
    latest_screenshots: latestScreenshots.map(s => ({ ...s, employee: { name: s.employee_name } }))
  });
});

router.get('/employees', requireLogin, (req, res) => {
  const employees = queryAll('SELECT * FROM employees');
  res.render('employees.html', { employees });
});

router.get('/employee/:id', requireLogin, (req, res) => {
  const employee = queryOne('SELECT * FROM employees WHERE id = ?', [parseInt(req.params.id)]);
  if (!employee) return res.redirect('/employees');

  const screenshots = queryAll('SELECT * FROM screenshots WHERE employee_id = ? ORDER BY captured_at DESC LIMIT 50', [parseInt(req.params.id)]);
  const activities = queryAll('SELECT * FROM activities WHERE employee_id = ? ORDER BY recorded_at DESC LIMIT 50', [parseInt(req.params.id)]);
  const alerts = queryAll('SELECT * FROM alerts WHERE employee_id = ? ORDER BY created_at DESC LIMIT 20', [parseInt(req.params.id)]);

  res.render('employee_detail.html', {
    employee,
    screenshots: screenshots.map(s => ({ ...s, employee_name: employee.name })),
    activities,
    alerts
  });
});

router.post('/api/employees/add', requireLogin, (req, res) => {
  const { name, email, department } = req.body;
  if (!name || !email) {
    req.session.flash = [{ category: 'danger', message: 'Name and email are required' }];
    return res.redirect('/employees');
  }

  const existing = queryOne('SELECT id FROM employees WHERE email = ?', [email]);
  if (existing) {
    req.session.flash = [{ category: 'danger', message: 'Employee with this email already exists' }];
    return res.redirect('/employees');
  }

  const agentKey = crypto.randomBytes(32).toString('hex');
  runSql('INSERT INTO employees (name, email, department, agent_key, consent_given, consent_date) VALUES (?, ?, ?, ?, 1, datetime("now"))', [name, email, department || '', agentKey]);

  req.session.flash = [{ category: 'success', message: `Employee ${name} added successfully!` }];
  res.redirect('/employees');
});

router.post('/api/employees/:id/edit', requireLogin, (req, res) => {
  const { name, email, department } = req.body;
  runSql('UPDATE employees SET name = ?, email = ?, department = ? WHERE id = ?', [name, email, department || '', parseInt(req.params.id)]);

  req.session.flash = [{ category: 'success', message: 'Employee updated!' }];
  res.redirect(`/employee/${req.params.id}`);
});

router.post('/api/employees/:id/delete', requireLogin, (req, res) => {
  const id = parseInt(req.params.id);
  runSql('DELETE FROM screenshots WHERE employee_id = ?', [id]);
  runSql('DELETE FROM activities WHERE employee_id = ?', [id]);
  runSql('DELETE FROM alerts WHERE employee_id = ?', [id]);
  runSql('DELETE FROM employees WHERE id = ?', [id]);

  req.session.flash = [{ category: 'success', message: 'Employee deleted!' }];
  res.redirect('/employees');
});

router.post('/api/employees/:id/regenerate-key', requireLogin, (req, res) => {
  const newKey = crypto.randomBytes(32).toString('hex');
  runSql('UPDATE employees SET agent_key = ? WHERE id = ?', [newKey, parseInt(req.params.id)]);

  req.session.flash = [{ category: 'success', message: 'Agent key regenerated!' }];
  res.redirect(`/employee/${req.params.id}`);
});

router.get('/api/dashboard-data', requireLogin, (req, res) => {
  const employees = queryAll('SELECT * FROM employees');
  const empData = employees.map(emp => {
    const latest = queryOne('SELECT * FROM activities WHERE employee_id = ? ORDER BY recorded_at DESC LIMIT 1', [emp.id]);
    return {
      id: emp.id,
      name: emp.name,
      status: emp.status,
      last_activity: latest ? latest.recorded_at : null,
      idle_time: latest ? latest.idle_time : 0
    };
  });

  const activeCount = employees.filter(e => e.status === 'active').length;
  const alertCount = queryOne('SELECT COUNT(*) as count FROM alerts WHERE is_read = 0').count;

  res.json({ employees: empData, total: employees.length, active: activeCount, alerts: alertCount });
});

module.exports = router;
