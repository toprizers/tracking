const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const { queryAll, queryOne, runSql } = require('../db');
const { requireLogin } = require('../middleware/auth');

router.get('/settings', requireLogin, (req, res) => {
  const users = queryAll('SELECT * FROM users');
  res.render('settings.html', { users });
});

router.post('/settings/change-password', requireLogin, (req, res) => {
  const { old_password, new_password, confirm_password } = req.body;
  const user = queryOne('SELECT * FROM users WHERE id = ?', [req.session.user.id]);

  if (!bcrypt.compareSync(old_password, user.password_hash)) {
    req.session.flash = [{ category: 'danger', message: 'Current password is incorrect' }];
    return res.redirect('/settings');
  }

  if (new_password !== confirm_password) {
    req.session.flash = [{ category: 'danger', message: 'New passwords do not match' }];
    return res.redirect('/settings');
  }

  if (new_password.length < 6) {
    req.session.flash = [{ category: 'danger', message: 'Password must be at least 6 characters' }];
    return res.redirect('/settings');
  }

  const hash = bcrypt.hashSync(new_password, 10);
  runSql('UPDATE users SET password_hash = ? WHERE id = ?', [hash, req.session.user.id]);
  req.session.flash = [{ category: 'success', message: 'Password changed successfully!' }];
  res.redirect('/settings');
});

module.exports = router;
