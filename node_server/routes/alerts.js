const express = require('express');
const router = express.Router();
const { queryAll, runSql } = require('../db');
const { requireLogin } = require('../middleware/auth');

router.get('/alerts', requireLogin, (req, res) => {
  const alerts = queryAll(`
    SELECT a.*, e.name as employee_name FROM alerts a
    JOIN employees e ON a.employee_id = e.id
    ORDER BY a.created_at DESC LIMIT 100
  `);
  res.render('alerts.html', { alerts });
});

router.get('/api/alerts', requireLogin, (req, res) => {
  const alerts = queryAll(`
    SELECT a.*, e.name as employee_name FROM alerts a
    JOIN employees e ON a.employee_id = e.id
    ORDER BY a.created_at DESC LIMIT 50
  `);
  res.json(alerts);
});

router.post('/api/alerts/:id/read', requireLogin, (req, res) => {
  runSql('UPDATE alerts SET is_read = 1 WHERE id = ?', [parseInt(req.params.id)]);
  res.json({ status: 'ok' });
});

router.post('/api/alerts/read-all', requireLogin, (req, res) => {
  runSql('UPDATE alerts SET is_read = 1 WHERE is_read = 0');
  res.json({ status: 'ok' });
});

module.exports = router;
