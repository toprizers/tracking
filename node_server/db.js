const initSqlJs = require('sql.js');
const path = require('path');
const bcrypt = require('bcryptjs');
const fs = require('fs');

const DATA_DIR = path.join(__dirname, 'data');
fs.mkdirSync(DATA_DIR, { recursive: true });

const UPLOAD_DIR = path.join(__dirname, 'uploads');
fs.mkdirSync(UPLOAD_DIR, { recursive: true });
fs.mkdirSync(path.join(UPLOAD_DIR, 'tmp'), { recursive: true });

const DB_PATH = path.join(DATA_DIR, 'employee_monitor.db');

let db = null;

async function initDatabase() {
  const SQL = await initSqlJs();

  if (fs.existsSync(DB_PATH)) {
    const buffer = fs.readFileSync(DB_PATH);
    db = new SQL.Database(buffer);
  } else {
    db = new SQL.Database();
  }

  db.run('PRAGMA foreign_keys = ON');

  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT DEFAULT 'admin',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS employees (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      emp_id TEXT UNIQUE,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      department TEXT,
      designation TEXT,
      role TEXT DEFAULT 'employee',
      reports_to INTEGER,
      laptop_id TEXT,
      status TEXT DEFAULT 'offline',
      agent_key TEXT UNIQUE NOT NULL,
      break_start TEXT,
      break_end TEXT,
      work_start TEXT DEFAULT '09:00',
      work_end TEXT DEFAULT '18:00',
      consent_given INTEGER DEFAULT 0,
      consent_date DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (reports_to) REFERENCES employees(id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS screenshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER NOT NULL,
      filename TEXT NOT NULL,
      filepath TEXT NOT NULL,
      thumbnail TEXT,
      captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS activities (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER NOT NULL,
      activity_type TEXT NOT NULL DEFAULT 'general',
      details TEXT,
      mouse_clicks INTEGER DEFAULT 0,
      keystrokes INTEGER DEFAULT 0,
      mouse_movement REAL DEFAULT 0,
      idle_time INTEGER DEFAULT 0,
      active_window TEXT,
      recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS alerts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER NOT NULL,
      alert_type TEXT NOT NULL,
      message TEXT NOT NULL,
      severity TEXT DEFAULT 'warning',
      is_read INTEGER DEFAULT 0,
      notified_to TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT
    )
  `);

  const result = db.exec('SELECT id FROM users WHERE username = "admin"');
  if (!result.length || result[0].values.length === 0) {
    const hash = bcrypt.hashSync('admin123', 10);
    db.run('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', ['admin', hash, 'admin']);
    console.log('[OK] Default admin created -> admin / admin123');
  }

  db.run("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_cleanup_days', '2')");
  db.run("INSERT OR IGNORE INTO settings (key, value) VALUES ('idle_alert_threshold', '300')");
  db.run("INSERT OR IGNORE INTO settings (key, value) VALUES ('work_start', '09:00')");
  db.run("INSERT OR IGNORE INTO settings (key, value) VALUES ('work_end', '18:00')");

  try { db.run("ALTER TABLE employees ADD COLUMN emp_id TEXT"); } catch(e) {}
  try { db.run("ALTER TABLE employees ADD COLUMN designation TEXT"); } catch(e) {}
  try { db.run("ALTER TABLE employees ADD COLUMN role TEXT DEFAULT 'employee'"); } catch(e) {}
  try { db.run("ALTER TABLE employees ADD COLUMN reports_to INTEGER"); } catch(e) {}
  try { db.run("ALTER TABLE employees ADD COLUMN break_start TEXT"); } catch(e) {}
  try { db.run("ALTER TABLE employees ADD COLUMN break_end TEXT"); } catch(e) {}
  try { db.run("ALTER TABLE employees ADD COLUMN work_start TEXT DEFAULT '09:00'"); } catch(e) {}
  try { db.run("ALTER TABLE employees ADD COLUMN work_end TEXT DEFAULT '18:00'"); } catch(e) {}
  try { db.run("ALTER TABLE alerts ADD COLUMN notified_to TEXT"); } catch(e) {}

  const empResult = db.exec('SELECT id FROM employees WHERE id = 1');
  if (!empResult.length || empResult[0].values.length === 0) {
    const agentKey = '04e4a5a877253f6f1301aec1075951025edf8c8768ee84ff0eed50629f5d85ac';
    db.run('INSERT INTO employees (emp_id, name, email, department, designation, role, agent_key, consent_given, consent_date) VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime("now"))',
      ['EMP001', 'Demo', 'demo@example.com', 'General', 'Employee', 'employee', agentKey]);
    console.log('[OK] Default employee created -> Demo / EMP001');
  }

  saveDatabase();
  console.log('[OK] Database initialized');
}

function cleanupOldData() {
  try {
    const daysSetting = queryOne("SELECT value FROM settings WHERE key = 'auto_cleanup_days'");
    const days = daysSetting ? parseInt(daysSetting.value) : 2;
    const cutoff = `datetime('now', '-${days} days')`;

    db.run(`DELETE FROM screenshots WHERE captured_at < ${cutoff}`);
    db.run(`DELETE FROM activities WHERE recorded_at < ${cutoff}`);
    db.run(`DELETE FROM alerts WHERE created_at < ${cutoff}`);
    saveDatabase();
    console.log(`[OK] Cleaned up data older than ${days} days`);
  } catch (err) {
    console.error('[ERROR] Cleanup failed:', err);
  }
}

function saveDatabase() {
  if (db) {
    const data = db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(DB_PATH, buffer);
  }
}

function queryAll(sql, params = []) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  const rows = [];
  while (stmt.step()) {
    rows.push(stmt.getAsObject());
  }
  stmt.free();
  return rows;
}

function queryOne(sql, params = []) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  let row = null;
  if (stmt.step()) {
    row = stmt.getAsObject();
  }
  stmt.free();
  return row;
}

function runSql(sql, params = []) {
  db.run(sql, params);
  saveDatabase();
}

module.exports = { db, initDatabase, UPLOAD_DIR, queryAll, queryOne, runSql, saveDatabase, cleanupOldData };
