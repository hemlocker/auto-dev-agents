const express = require('express');
const router = express.Router();
const deviceTypeController = require('../controllers/deviceTypeController');

// GET /api/device-types - 获取设备类型列表
router.get('/device-types', deviceTypeController.getDeviceTypes);

// GET /api/device-types/all - 获取所有设备类型（用于下拉选择器）
router.get('/device-types/all', deviceTypeController.getAllDeviceTypes);

// POST /api/device-types - 新增设备类型
router.post('/device-types', deviceTypeController.createDeviceType);

// GET /api/device-types/:id - 获取设备类型详情
router.get('/device-types/:id', deviceTypeController.getDeviceTypeById);

// PUT /api/device-types/:id - 更新设备类型
router.put('/device-types/:id', deviceTypeController.updateDeviceType);

// DELETE /api/device-types/:id - 删除设备类型
router.delete('/device-types/:id', deviceTypeController.deleteDeviceType);

module.exports = router;
