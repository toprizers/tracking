const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const { queryOne, runSql } = require('../db');
const { requireLogin } = require('../middleware/auth');

router.get('/login', (req, res) => {
  if (req.session.user) return res.redirect('/');
  res.render('login.html', { layout: false });
});

router.post('/login', (req, res) => {
  const { username, password, remember } = req.body;
  const user = queryOne('SELECT * FROM users WHERE username = ?', [username]);

  if (user && bcrypt.compareSync(password, user.password_hash)) {
    req.session.user = { id: user.id, username: user.username, role: user.role };
    if (remember) req.session.cookie.maxAge = 7 * 24 * 60 * 60 * 1000;
    return res.redirect('/');
  }

  req.session.flash = [{ category: 'danger', message: 'Invalid username or password' }];
  res.redirect('/login');
});

router.get('/logout', requireLogin, (req, res) => {
  req.session.destroy();
  res.redirect('/login');
});

module.exports = router;
