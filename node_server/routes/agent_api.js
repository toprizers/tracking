const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { UPLOAD_DIR, queryOne, runSql } = require('../db');

const upload = multer({
  dest: path.join(__dirname, '..', 'uploads', 'tmp'),
  limits: { fileSize: 16 * 1024 * 1024 }
});

function verifyAgent(key) {
  if (!key) return null;
  const employee = queryOne('SELECT * FROM employees WHERE agent_key = ?', [key]);
  if (!employee) return null;
  runSql('UPDATE employees SET status = ? WHERE id = ?', ['active', employee.id]);
  return employee;
}

function isBreakTime(employee) {
  if (!employee.break_start || !employee.break_end) return false;
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const currentTime = `${hours}:${minutes}`;
  return currentTime >= employee.break_start && currentTime <= employee.break_end;
}

function isWorkingHours(employee) {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const currentTime = `${hours}:${minutes}`;
  const start = employee.work_start || '09:00';
  const end = employee.work_end || '18:00';
  return currentTime >= start && currentTime <= end;
}

function getNotificationChain(employee) {
  const chain = [];
  if (employee.reports_to) {
    const manager = queryOne('SELECT * FROM employees WHERE id = ?', [employee.reports_to]);
    if (manager) {
      chain.push({ name: manager.name, role: manager.role, id: manager.id });
      if (manager.reports_to) {
        const tl = queryOne('SELECT * FROM employees WHERE id = ?', [manager.reports_to]);
        if (tl) {
          chain.push({ name: tl.name, role: tl.role, id: tl.id });
          if (tl.reports_to) {
            const hr = queryOne('SELECT * FROM employees WHERE id = ?', [tl.reports_to]);
            if (hr) chain.push({ name: hr.name, role: hr.role, id: hr.id });
          }
        }
      }
    }
  }
  const hrEmployees = queryAll("SELECT * FROM employees WHERE role = 'hr'");
  hrEmployees.forEach(hr => {
    if (!chain.find(c => c.id === hr.id)) {
      chain.push({ name: hr.name, role: hr.role, id: hr.id });
    }
  });
  return chain;
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

  try {
    const empDir = path.join(UPLOAD_DIR, String(employee.id));
    fs.mkdirSync(empDir, { recursive: true });
    const filename = `${employee.id}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}.png`;
    const filepath = path.join(empDir, filename);
    fs.renameSync(req.file.path, filepath);

    const relPath = `${employee.id}/${filename}`;
    runSql('INSERT INTO screenshots (employee_id, filename, filepath, captured_at) VALUES (?, ?, ?, datetime("now"))', [employee.id, filename, relPath]);

    const io = req.app.get('io');
    io.emit('new_screenshot', {
      employee_id: employee.id,
      employee_name: employee.name,
      emp_id: employee.emp_id,
      department: employee.department,
      filename,
      filepath: relPath,
      timestamp: new Date().toISOString()
    });

    res.json({ status: 'ok', filename });
  } catch (err) {
    console.error('Screenshot save error:', err);
    if (req.file && fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
    res.status(500).json({ error: 'Save failed' });
  }
});

router.post('/api/agent/activity', (req, res) => {
  const { agent_key, type, mouse_clicks, keystrokes, mouse_movement, idle_time, active_window } = req.body;
  const employee = verifyAgent(agent_key);
  if (!employee) return res.status(401).json({ error: 'Invalid key' });

  runSql('INSERT INTO activities (employee_id, activity_type, mouse_clicks, keystrokes, mouse_movement, idle_time, active_window, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime("now"))',
    [employee.id, type || 'general', mouse_clicks || 0, keystrokes || 0, mouse_movement || 0, idle_time || 0, active_window || null]);

  const io = req.app.get('io');

  const breakTime = isBreakTime(employee);
  const workingHours = isWorkingHours(employee);

  if ((idle_time || 0) >= 300 && workingHours && !breakTime) {
    const existing = queryOne('SELECT id FROM alerts WHERE employee_id = ? AND alert_type = ? AND created_at >= datetime("now", "-10 minutes")', [employee.id, 'idle']);
    if (!existing) {
      const idleMinutes = Math.floor(idle_time / 60);
      const message = `${employee.name} (${employee.emp_id || 'N/A'}) has been idle for ${idleMinutes} minutes during working hours`;

      const chain = getNotificationChain(employee);
      const notifiedTo = chain.map(c => `${c.name}(${c.role})`).join(', ');

      runSql('INSERT INTO alerts (employee_id, alert_type, message, severity, notified_to) VALUES (?, ?, ?, ?, ?)',
        [employee.id, 'idle', message, 'warning', notifiedTo]);

      io.emit('new_alert', {
        employee_id: employee.id,
        employee_name: employee.name,
        emp_id: employee.emp_id,
        department: employee.department,
        type: 'idle',
        message,
        severity: 'warning',
        notified_to: notifiedTo,
        timestamp: new Date().toISOString()
      });

      chain.forEach(person => {
        io.emit('manager_alert', {
          notify_to: person.id,
          notify_name: person.name,
          notify_role: person.role,
          employee_name: employee.name,
          emp_id: employee.emp_id,
          department: employee.department,
          message,
          timestamp: new Date().toISOString()
        });
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

  try {
    const buffer = fs.readFileSync(req.file.path);
    fs.unlinkSync(req.file.path);
    const b64 = buffer.toString('base64');
    const io = req.app.get('io');
    io.emit('live_screen', {
      employee_id: employee.id,
      employee_name: employee.name,
      emp_id: employee.emp_id,
      department: employee.department,
      image: b64,
      timestamp: new Date().toISOString()
    });
    res.json({ status: 'ok' });
  } catch (err) {
    console.error('Live screen error:', err);
    if (req.file && fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
    res.status(500).json({ error: 'Failed' });
  }
});

module.exports = router;
