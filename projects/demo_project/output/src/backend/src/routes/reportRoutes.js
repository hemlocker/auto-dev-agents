const express = require('express');
const router = express.Router();
const reportController = require('../controllers/reportController');

// GET /api/reports/statistics - 获取统计数据
router.get('/reports/statistics', reportController.getStatistics);

module.exports = router;
