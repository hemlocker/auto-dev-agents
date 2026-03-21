const Device = require('../../models/Device');
const { Op } = require('sequelize');

// 获取设备列表（支持搜索和筛选）
exports.getDevices = async (req, res) => {
  try {
    const { keyword, device_type, status, department, user_name, page = 1, pageSize = 10 } = req.query;
    
    // 构建查询条件
    const where = {};
    
    if (keyword) {
      where[Op.or] = [
        { device_name: { [Op.like]: `%${keyword}%` } },
        { device_id: { [Op.like]: `%${keyword}%` } }
      ];
    }
    
    if (device_type) {
      where.device_type = device_type;
    }
    
    if (status) {
      where.status = status;
    }
    
    if (department) {
      where.department = department;
    }
    
    if (user_name) {
      where.user_name = { [Op.like]: `%${user_name}%` };
    }
    
    // 分页
    const offset = (page - 1) * pageSize;
    const limit = parseInt(pageSize);
    
    const { count, rows } = await Device.findAndCountAll({
      where,
      offset,
      limit,
      order: [['device_id', 'ASC']]
    });
    
    res.json({
      code: 200,
      message: 'success',
      data: {
        list: rows,
        total: count,
        page: parseInt(page),
        pageSize: limit
      }
    });
  } catch (error) {
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 获取设备详情
exports.getDeviceById = async (req, res) => {
  try {
    const { id } = req.params;
    const device = await Device.findByPk(id);
    
    if (!device) {
      return res.status(404).json({
        code: 404,
        message: '设备不存在',
        data: null
      });
    }
    
    res.json({
      code: 200,
      message: 'success',
      data: device
    });
  } catch (error) {
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 新增设备
exports.createDevice = async (req, res) => {
  try {
    const { device_id } = req.body;
    
    // 检查设备编号是否已存在
    const existing = await Device.findByPk(device_id);
    if (existing) {
      return res.status(400).json({
        code: 400,
        message: '设备编号已存在',
        data: null
      });
    }
    
    const device = await Device.create(req.body);
    
    res.json({
      code: 200,
      message: '新增成功',
      data: {
        device_id: device.device_id
      }
    });
  } catch (error) {
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 更新设备
exports.updateDevice = async (req, res) => {
  try {
    const { id } = req.params;
    const device = await Device.findByPk(id);
    
    if (!device) {
      return res.status(404).json({
        code: 404,
        message: '设备不存在',
        data: null
      });
    }
    
    // 不允许修改设备编号
    delete req.body.device_id;
    
    await device.update(req.body);
    
    res.json({
      code: 200,
      message: '更新成功',
      data: {
        device_id: id
      }
    });
  } catch (error) {
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 删除设备
exports.deleteDevice = async (req, res) => {
  try {
    const { id } = req.params;
    const device = await Device.findByPk(id);
    
    if (!device) {
      return res.status(404).json({
        code: 404,
        message: '设备不存在',
        data: null
      });
    }
    
    await device.destroy();
    
    res.json({
      code: 200,
      message: '删除成功',
      data: null
    });
  } catch (error) {
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};
