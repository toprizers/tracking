const express = require('express');
const router = express.Router();
const { queryAll, queryOne } = require('../db');
const { requireLogin } = require('../middleware/auth');

router.get('/reports', requireLogin, (req, res) => {
  const employees = queryAll('SELECT * FROM employees');
  res.render('reports.html', { employees });
});

router.get('/api/reports/activity/:empId', requireLogin, (req, res) => {
  const days = parseInt(req.query.days) || 7;
  const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

  const activities = queryAll('SELECT * FROM activities WHERE employee_id = ? AND recorded_at >= ? ORDER BY recorded_at ASC', [parseInt(req.params.empId), startDate]);

  const dailyData = {};
  for (const act of activities) {
    const day = act.recorded_at.split(' ')[0];
    if (!dailyData[day]) dailyData[day] = { clicks: 0, keys: 0, idle_minutes: 0, active_minutes: 0 };
    dailyData[day].clicks += act.mouse_clicks;
    dailyData[day].keys += act.keystrokes;
    dailyData[day].idle_minutes += Math.floor(act.idle_time / 60);
    if (act.idle_time < 300) dailyData[day].active_minutes += 1;
  }

  const labels = Object.keys(dailyData).sort();
  res.json({
    labels,
    clicks: labels.map(d => dailyData[d].clicks),
    keystrokes: labels.map(d => dailyData[d].keys),
    idle_minutes: labels.map(d => dailyData[d].idle_minutes),
    active_minutes: labels.map(d => dailyData[d].active_minutes)
  });
});

router.get('/api/reports/screenshots/:empId', requireLogin, (req, res) => {
  const days = parseInt(req.query.days) || 7;
  const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

  const screenshots = queryAll('SELECT * FROM screenshots WHERE employee_id = ? AND captured_at >= ?', [parseInt(req.params.empId), startDate]);

  const daily = {};
  for (const s of screenshots) {
    const day = s.captured_at.split(' ')[0];
    daily[day] = (daily[day] || 0) + 1;
  }

  const labels = Object.keys(daily).sort();
  res.json({ labels, counts: labels.map(d => daily[d]) });
});

router.get('/api/reports/summary', requireLogin, (req, res) => {
  const days = parseInt(req.query.days) || 7;
  const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
  const employees = queryAll('SELECT * FROM employees');

  const summary = employees.map(emp => {
    const actCount = queryOne('SELECT COUNT(*) as count FROM activities WHERE employee_id = ? AND recorded_at >= ?', [emp.id, startDate]).count;
    const ssCount = queryOne('SELECT COUNT(*) as count FROM screenshots WHERE employee_id = ? AND captured_at >= ?', [emp.id, startDate]).count;
    const latest = queryOne('SELECT * FROM activities WHERE employee_id = ? ORDER BY recorded_at DESC LIMIT 1', [emp.id]);
    const totalClicks = queryOne('SELECT COALESCE(SUM(mouse_clicks), 0) as total FROM activities WHERE employee_id = ? AND recorded_at >= ?', [emp.id, startDate]).total;
    const totalKeys = queryOne('SELECT COALESCE(SUM(keystrokes), 0) as total FROM activities WHERE employee_id = ? AND recorded_at >= ?', [emp.id, startDate]).total;

    return {
      id: emp.id, name: emp.name, department: emp.department, status: emp.status,
      activity_count: actCount, screenshot_count: ssCount,
      total_clicks: totalClicks, total_keys: totalKeys,
      last_active: latest ? latest.recorded_at : null
    };
  });

  res.json({ summary, days });
});

module.exports = router;
