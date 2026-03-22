const express = require('express');
const router = express.Router();
const printController = require('../controllers/printController');

// GET /api/devices/:id/label - 获取设备标签数据
router.get('/devices/:id/label', printController.getLabelData);

// POST /api/devices/print-batch - 批量打印设备标签
router.post('/devices/print-batch', printController.printBatchLabels);

module.exports = router;
