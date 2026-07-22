const express = require('express');
const session = require('express-session');
const nunjucks = require('nunjucks');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const { initDatabase, UPLOAD_DIR, cleanupOldData } = require('./db');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const env = nunjucks.configure('views', {
  autoescape: true,
  express: app,
  watch: false
});

env.addFilter('dateFormat', (date, format) => {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  if (format === '%d %b, %H:%M') {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${d.getDate()} ${months[d.getMonth()]}, ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
  if (format === '%d %b %Y, %H:%M') {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
  if (format === '%H:%M') {
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
  return d.toISOString();
});

app.set('view engine', 'njk');
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(UPLOAD_DIR));

app.use(session({
  secret: process.env.SESSION_SECRET || 'employee-monitor-secret-change-this',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000 }
}));

app.use((req, res, next) => {
  res.locals.current_user = req.session.user || null;
  res.locals.flash = req.session.flash || [];
  req.session.flash = [];
  next();
});

const urlMap = {
  'auth.login': '/login',
  'auth.logout': '/logout',
  'employees.dashboard': '/',
  'employees.employees_list': '/employees',
  'screenshots.screenshots_page': '/screenshots',
  'reports.reports_page': '/reports',
  'alerts.alerts_page': '/alerts',
  'settings.settings_page': '/settings'
};

app.use((req, res, next) => {
  res.locals.url_for = (routeName, params) => {
    if (routeName === 'employees.employee_detail' && params && params.emp_id) {
      return `/employee/${params.emp_id}`;
    }
    return urlMap[routeName] || '/';
  };
  next();
});

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  socket.on('disconnect', () => console.log('Client disconnected:', socket.id));
});

app.set('io', io);

const authRoutes = require('./routes/auth');
const employeeRoutes = require('./routes/employees');
const agentApiRoutes = require('./routes/agent_api');
const screenshotRoutes = require('./routes/screenshots');
const alertRoutes = require('./routes/alerts');
const reportRoutes = require('./routes/reports');
const settingsRoutes = require('./routes/settings');

app.use(authRoutes);
app.use(employeeRoutes);
app.use(agentApiRoutes);
app.use(screenshotRoutes);
app.use(alertRoutes);
app.use(reportRoutes);
app.use(settingsRoutes);

const PORT = process.env.PORT || 5000;

initDatabase().then(() => {
  server.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running at http://localhost:${PORT}`);
    console.log('Login: admin / admin123');
  });

  cleanupOldData();
  setInterval(cleanupOldData, 24 * 60 * 60 * 1000);
}).catch(err => {
  console.error('Failed to initialize database:', err);
  process.exit(1);
});
