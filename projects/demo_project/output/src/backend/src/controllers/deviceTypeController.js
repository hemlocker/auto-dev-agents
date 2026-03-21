const DeviceType = require('../../models/DeviceType');
const { Op } = require('sequelize');

// 获取设备类型列表
exports.getDeviceTypes = async (req, res) => {
  try {
    const { keyword, is_active, page = 1, pageSize = 10 } = req.query;
    
    // 构建查询条件
    const where = {};
    
    if (keyword) {
      where.type_name = { [Op.like]: `%${keyword}%` };
    }
    
    if (is_active !== undefined) {
      where.is_active = is_active === 'true';
    }
    
    // 分页
    const offset = (page - 1) * pageSize;
    const limit = parseInt(pageSize);
    
    const { count, rows } = await DeviceType.findAndCountAll({
      where,
      offset,
      limit,
      order: [['sort_order', 'ASC'], ['type_id', 'ASC']]
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
    console.error('获取设备类型列表失败:', error);
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 获取所有设备类型（用于下拉选择器）
exports.getAllDeviceTypes = async (req, res) => {
  try {
    const types = await DeviceType.findAll({
      where: { is_active: true },
      order: [['sort_order', 'ASC'], ['type_id', 'ASC']]
    });
    
    res.json({
      code: 200,
      message: 'success',
      data: types
    });
  } catch (error) {
    console.error('获取所有设备类型失败:', error);
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 获取设备类型详情
exports.getDeviceTypeById = async (req, res) => {
  try {
    const { id } = req.params;
    const deviceType = await DeviceType.findByPk(id);
    
    if (!deviceType) {
      return res.status(404).json({
        code: 404,
        message: '设备类型不存在',
        data: null
      });
    }
    
    res.json({
      code: 200,
      message: 'success',
      data: deviceType
    });
  } catch (error) {
    console.error('获取设备类型详情失败:', error);
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 新增设备类型
exports.createDeviceType = async (req, res) => {
  try {
    const { type_name } = req.body;
    
    // 检查设备类型名称是否已存在
    const existing = await DeviceType.findOne({ where: { type_name } });
    if (existing) {
      return res.status(400).json({
        code: 400,
        message: '设备类型名称已存在',
        data: null
      });
    }
    
    const deviceType = await DeviceType.create(req.body);
    
    res.json({
      code: 200,
      message: '新增成功',
      data: {
        type_id: deviceType.type_id
      }
    });
  } catch (error) {
    console.error('新增设备类型失败:', error);
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 更新设备类型
exports.updateDeviceType = async (req, res) => {
  try {
    const { id } = req.params;
    const deviceType = await DeviceType.findByPk(id);
    
    if (!deviceType) {
      return res.status(404).json({
        code: 404,
        message: '设备类型不存在',
        data: null
      });
    }
    
    // 如果修改了名称，检查是否与其他类型重复
    if (req.body.type_name && req.body.type_name !== deviceType.type_name) {
      const existing = await DeviceType.findOne({
        where: {
          type_name: req.body.type_name,
          type_id: { [Op.ne]: id }
        }
      });
      if (existing) {
        return res.status(400).json({
          code: 400,
          message: '设备类型名称已存在',
          data: null
        });
      }
    }
    
    await deviceType.update(req.body);
    
    res.json({
      code: 200,
      message: '更新成功',
      data: {
        type_id: id
      }
    });
  } catch (error) {
    console.error('更新设备类型失败:', error);
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};

// 删除设备类型
exports.deleteDeviceType = async (req, res) => {
  try {
    const { id } = req.params;
    const deviceType = await DeviceType.findByPk(id);
    
    if (!deviceType) {
      return res.status(404).json({
        code: 404,
        message: '设备类型不存在',
        data: null
      });
    }
    
    await deviceType.destroy();
    
    res.json({
      code: 200,
      message: '删除成功',
      data: null
    });
  } catch (error) {
    console.error('删除设备类型失败:', error);
    res.status(500).json({
      code: 500,
      message: '服务器内部错误',
      data: null
    });
  }
};
