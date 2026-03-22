const express = require('express');
const router = express.Router();
const exportController = require('../controllers/exportController');

// GET /api/devices/export - 导出设备数据
router.get('/devices/export', exportController.exportDevices);

module.exports = router;
