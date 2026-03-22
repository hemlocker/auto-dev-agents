const express = require('express');
const router = express.Router();
const importController = require('../controllers/importController');
const multer = require('multer');

// 配置 multer 内存存储
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB 限制
  }
});

// GET /api/devices/import-template - 下载导入模板
router.get('/devices/import-template', importController.downloadTemplate);

// POST /api/devices/import - 批量导入设备
router.post('/devices/import', upload.single('file'), importController.importDevices);

module.exports = router;
