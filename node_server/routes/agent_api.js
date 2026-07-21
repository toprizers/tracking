const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { UPLOAD_DIR, queryOne, runSql } = require('../db');

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 16 * 1024 * 1024 } });

function verifyAgent(key) {
  if (!key) return null;
  const employee = queryOne('SELECT * FROM employees WHERE agent_key = ?', [key]);
  if (!employee) return null;
  runSql('UPDATE employees SET status = ? WHERE id = ?', ['active', employee.id]);
  return employee;
}

router.post('/api/agent/heartbeat', (req, res) => {
  const { agent_key } = req.body;
  const employee = verifyAgent(agent_key);
  if (!employee) return res.status(401).json({ error: 'Invalid key' });

  runSql('UPDATE employees SET status = ? WHERE id = ?', ['active', employee.id]);

  const io = req.app.get('io');
  io.emit('agent_heartbeat', {
    employee_id: employee.id,
    employee_name: employee.name,
    timestamp: new Date().toISOString()
  });

  res.json({ status: 'ok' });
});

router.post('/api/agent/screenshot', upload.single('screenshot'), (req, res) => {
  const key = req.body.agent_key;
  const employee = verifyAgent(key);
  if (!employee) return res.status(401).json({ error: 'Invalid key' });
  if (!req.file) return res.status(400).json({ error: 'No screenshot' });

  const empDir = path.join(UPLOAD_DIR, String(employee.id));
  fs.mkdirSync(empDir, { recursive: true });
  const filename = `${employee.id}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}.png`;
  const filepath = path.join(empDir, filename);
  fs.writeFileSync(filepath, req.file.buffer);

  const relPath = `${employee.id}/${filename}`;
  runSql('INSERT INTO screenshots (employee_id, filename, filepath, captured_at) VALUES (?, ?, ?, datetime("now"))', [employee.id, filename, relPath]);

  const io = req.app.get('io');
  io.emit('new_screenshot', {
    employee_id: employee.id,
    employee_name: employee.name,
    filename,
    filepath: relPath,
    timestamp: new Date().toISOString()
  });

  res.json({ status: 'ok', filename });
});

router.post('/api/agent/activity', (req, res) => {
  const { agent_key, type, mouse_clicks, keystrokes, mouse_movement, idle_time, active_window } = req.body;
  const employee = verifyAgent(agent_key);
  if (!employee) return res.status(401).json({ error: 'Invalid key' });

  runSql('INSERT INTO activities (employee_id, activity_type, mouse_clicks, keystrokes, mouse_movement, idle_time, active_window, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime("now"))',
    [employee.id, type || 'general', mouse_clicks || 0, keystrokes || 0, mouse_movement || 0, idle_time || 0, active_window || null]);

  if ((idle_time || 0) >= 900) {
    const existing = queryOne('SELECT id FROM alerts WHERE employee_id = ? AND alert_type = ? AND created_at >= datetime("now", "-30 minutes")', [employee.id, 'idle']);
    if (!existing) {
      const message = `${employee.name} has been idle for ${Math.floor(idle_time / 60)} minutes`;
      runSql('INSERT INTO alerts (employee_id, alert_type, message, severity) VALUES (?, ?, ?, ?)', [employee.id, 'idle', message, 'warning']);

      const io = req.app.get('io');
      io.emit('new_alert', {
        employee_id: employee.id,
        employee_name: employee.name,
        type: 'idle',
        message,
        severity: 'warning',
        timestamp: new Date().toISOString()
      });
    }
  }

  res.json({ status: 'ok' });
});

router.post('/api/agent/input-status', (req, res) => {
  const { agent_key, mouse_works, keyboard_works } = req.body;
  const employee = verifyAgent(agent_key);
  if (!employee) return res.status(401).json({ error: 'Invalid key' });

  const failedDevices = [];
  if (mouse_works === false) failedDevices.push('mouse');
  if (keyboard_works === false) failedDevices.push('keyboard');

  const io = req.app.get('io');
  for (const device of failedDevices) {
    const msg = `${employee.name}'s ${device} is not responding!`;
    const existing = queryOne('SELECT id FROM alerts WHERE employee_id = ? AND alert_type = ? AND message = ? AND created_at >= datetime("now", "-30 minutes")', [employee.id, 'input_failure', msg]);
    if (!existing) {
      runSql('INSERT INTO alerts (employee_id, alert_type, message, severity) VALUES (?, ?, ?, ?)', [employee.id, 'input_failure', msg, 'critical']);

      io.emit('new_alert', {
        employee_id: employee.id,
        employee_name: employee.name,
        type: 'input_failure',
        message: msg,
        severity: 'critical',
        timestamp: new Date().toISOString()
      });
    }
  }

  res.json({ status: 'ok' });
});

router.post('/api/agent/status', (req, res) => {
  const { agent_key, status } = req.body;
  const employee = verifyAgent(agent_key);
  if (!employee) return res.status(401).json({ error: 'Invalid key' });

  runSql('UPDATE employees SET status = ? WHERE id = ?', [status || 'active', employee.id]);
  res.json({ status: 'ok' });
});

router.post('/api/agent/live-screen', upload.single('screenshot'), (req, res) => {
  const key = req.body.agent_key;
  const employee = verifyAgent(key);
  if (!employee) return res.status(401).json({ error: 'Invalid key' });
  if (!req.file) return res.status(400).json({ error: 'No screenshot' });

  const b64 = req.file.buffer.toString('base64');
  const io = req.app.get('io');
  io.emit('live_screen', {
    employee_id: employee.id,
    employee_name: employee.name,
    image: b64,
    timestamp: new Date().toISOString()
  });

  res.json({ status: 'ok' });
});

module.exports = router;
