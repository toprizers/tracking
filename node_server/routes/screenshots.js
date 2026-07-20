const express = require('express');
const router = express.Router();
const { queryAll, queryOne } = require('../db');
const { requireLogin } = require('../middleware/auth');

router.get('/screenshots', requireLogin, (req, res) => {
  const page = Math.max(1, parseInt(req.query.page) || 1);
  const perPage = 20;
  const offset = (page - 1) * perPage;

  const screenshots = queryAll(`
    SELECT s.*, e.name as employee_name FROM screenshots s
    JOIN employees e ON s.employee_id = e.id
    ORDER BY s.captured_at DESC LIMIT ? OFFSET ?
  `, [perPage, offset]);

  const total = queryOne('SELECT COUNT(*) as count FROM screenshots').count;
  const totalPages = Math.ceil(total / perPage);
  const employees = queryAll('SELECT * FROM employees');

  res.render('screenshots.html', {
    screenshots: {
      items: screenshots.map(s => ({ ...s, employee: { name: s.employee_name } })),
      page,
      pages: totalPages,
      has_prev: page > 1,
      has_next: page < totalPages,
      prev_num: page - 1,
      next_num: page + 1,
      iter_pages: () => {
        const pages = [];
        for (let i = 1; i <= totalPages; i++) pages.push(i);
        return pages;
      }
    },
    employees
  });
});

router.get('/api/screenshots/:empId', requireLogin, (req, res) => {
  const screenshots = queryAll('SELECT * FROM screenshots WHERE employee_id = ? ORDER BY captured_at DESC LIMIT 100', [parseInt(req.params.empId)]);
  res.json(screenshots);
});

module.exports = router;
