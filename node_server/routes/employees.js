const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const { queryAll, queryOne, runSql } = require('../db');
const { requireLogin } = require('../middleware/auth');

router.get('/', requireLogin, (req, res) => {
  try {
    const employees = queryAll('SELECT * FROM employees ORDER BY id');
    let totalAlerts = 0;
    try { totalAlerts = queryOne('SELECT COUNT(*) as count FROM alerts WHERE is_read = 0').count || 0; } catch(e) {}
    const latestScreenshots = queryAll(`
      SELECT s.*, e.name as employee_name, e.emp_id, e.department, e.designation FROM screenshots s
      JOIN employees e ON s.employee_id = e.id
      ORDER BY s.captured_at DESC LIMIT 8
    `);

    let recentAlerts = [];
    try {
      recentAlerts = queryAll(`
        SELECT a.*, e.name as employee_name, e.emp_id, e.department FROM alerts a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.is_read = 0
        ORDER BY a.created_at DESC LIMIT 10
      `);
    } catch(e) {}

    const activeCount = employees.filter(e => e.status === 'active').length;

    const grouped = {};
    employees.forEach(emp => {
      const role = emp.role || 'employee';
      if (!grouped[role]) grouped[role] = [];
      grouped[role].push(emp);
    });

    res.render('dashboard.html', {
      employees,
      grouped_employees: grouped,
      total_employees: employees.length,
      active_employees: activeCount,
      total_alerts: totalAlerts,
      recent_alerts: recentAlerts,
      latest_screenshots: latestScreenshots.map(s => ({
        ...s,
        employee: { name: s.employee_name, emp_id: s.emp_id, department: s.department, designation: s.designation }
      }))
    });
  } catch(err) {
    console.error('[DASHBOARD ERROR]', err);
    res.status(500).send('Dashboard Error: ' + err.message);
  }
});

router.get('/employees', requireLogin, (req, res) => {
  const employees = queryAll('SELECT * FROM employees ORDER BY id');
  res.render('employees.html', { employees });
});

router.get('/employee/:id', requireLogin, (req, res) => {
  const employee = queryOne('SELECT * FROM employees WHERE id = ?', [parseInt(req.params.id)]);
  if (!employee) return res.redirect('/employees');

  const manager = employee.reports_to ? queryOne('SELECT name FROM employees WHERE id = ?', [employee.reports_to]) : null;

  const screenshots = queryAll('SELECT * FROM screenshots WHERE employee_id = ? ORDER BY captured_at DESC LIMIT 50', [parseInt(req.params.id)]);
  const activities = queryAll('SELECT * FROM activities WHERE employee_id = ? ORDER BY recorded_at DESC LIMIT 50', [parseInt(req.params.id)]);
  const alerts = queryAll('SELECT * FROM alerts WHERE employee_id = ? ORDER BY created_at DESC LIMIT 20', [parseInt(req.params.id)]);

  const allEmployees = queryAll('SELECT id, name, emp_id, role FROM employees ORDER BY name');

  res.render('employee_detail.html', {
    employee,
    manager,
    screenshots: screenshots.map(s => ({ ...s, employee_name: employee.name })),
    activities,
    alerts,
    allEmployees
  });
});

router.post('/api/employees/add', requireLogin, (req, res) => {
  const { emp_id, name, email, department, designation, role, reports_to, work_start, work_end } = req.body;
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
  const finalEmpId = emp_id || `EMP${String(Date.now()).slice(-4)}`;

  runSql('INSERT INTO employees (emp_id, name, email, department, designation, role, reports_to, agent_key, work_start, work_end, consent_given, consent_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime("now"))',
    [finalEmpId, name, email, department || '', designation || '', role || 'employee', reports_to || null, agentKey, work_start || '09:00', work_end || '18:00']);

  req.session.flash = [{ category: 'success', message: `Employee ${name} added! Agent Key: ${agentKey}` }];
  res.redirect('/employees');
});

router.post('/api/employees/:id/edit', requireLogin, (req, res) => {
  const { emp_id, name, email, department, designation, role, reports_to, work_start, work_end, break_start, break_end } = req.body;
  runSql('UPDATE employees SET emp_id=?, name=?, email=?, department=?, designation=?, role=?, reports_to=?, work_start=?, work_end=?, break_start=?, break_end=? WHERE id=?',
    [emp_id, name, email, department || '', designation || '', role || 'employee', reports_to || null, work_start || '09:00', work_end || '18:00', break_start || null, break_end || null, parseInt(req.params.id)]);

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

  req.session.flash = [{ category: 'success', message: `Agent key regenerated! New key: ${newKey}` }];
  res.redirect(`/employee/${req.params.id}`);
});

router.get('/api/dashboard-data', requireLogin, (req, res) => {
  const employees = queryAll('SELECT * FROM employees');
  const empData = employees.map(emp => {
    const latest = queryOne('SELECT * FROM activities WHERE employee_id = ? ORDER BY recorded_at DESC LIMIT 1', [emp.id]);
    return {
      id: emp.id,
      emp_id: emp.emp_id,
      name: emp.name,
      department: emp.department,
      designation: emp.designation,
      role: emp.role,
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
