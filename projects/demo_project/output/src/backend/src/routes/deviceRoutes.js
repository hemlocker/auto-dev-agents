const express = require('express');
const router = express.Router();
const deviceController = require('../controllers/deviceController');

// GET /api/devices - 获取设备列表
router.get('/devices', deviceController.getDevices);

// POST /api/devices - 新增设备
router.post('/devices', deviceController.createDevice);

// GET /api/devices/:id - 获取设备详情
router.get('/devices/:id', deviceController.getDeviceById);

// PUT /api/devices/:id - 更新设备
router.put('/devices/:id', deviceController.updateDevice);

// DELETE /api/devices/:id - 删除设备
router.delete('/devices/:id', deviceController.deleteDevice);

module.exports = router;
