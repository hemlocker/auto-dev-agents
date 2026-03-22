const Device = require('../../models/Device');
const { Op } = require('sequelize');
const moment = require('moment');

/**
 * 获取统计数据
 */
exports.getStatistics = async (req, res) => {
  try {
    const { dimension, start_date, end_date } = req.query;
    
    if (!dimension) {
      return res.status(400).json({
        code: 400,
        message: '请提供统计维度',
        data: null
      });
    }

    // 构建时间范围查询条件
    const where = {};
    if (start_date || end_date) {
      where.purchase_date = {};
      if (start_date) {
        where.purchase_date[Op.gte] = start_date;
      }
      if (end_date) {
        where.purchase_date[Op.lte] = end_date;
      }
    }

    let result = null;

    switch (dimension) {
      case 'status':
        result = await getStatusStatistics(where);
        break;
      case 'department':
        result = await getDepartmentStatistics(where);
        break;
      case 'type':
        result = await getTypeStatistics(where);
        break;
      case 'time':
        result = await getTimeStatistics(where, start_date, end_date);
        break;
      default:
        return res.status(400).json({
          code: 400,
          message: '不支持的统计维度',
          data: null
        });
    }

    res.json({
      code: 200,
      message: 'success',
      data: result
    });
  } catch (error) {
    console.error('获取统计数据失败:', error);
    res.status(500).json({
      code: 500,
      message: '获取统计数据失败',
      data: null
    });
  }
};

/**
 * 按设备状态统计
 */
async function getStatusStatistics(where) {
  const results = await Device.findAll({
    attributes: [
      'status',
      [Device.sequelize.fn('COUNT', Device.sequelize.col('device_id')), 'count']
    ],
    where,
    group: ['status'],
    raw: true
  });

  const total = results.reduce((sum, item) => sum + parseInt(item.count), 0);
  const inUse = results.find(r => r.status === '在用')?.count || 0;
  const idle = results.find(r => r.status === '闲置')?.count || 0;
  const scrapped = results.find(r => r.status === '报废')?.count || 0;

  const details = results.map(item => ({
    status: item.status,
    count: parseInt(item.count),
    percentage: total > 0 ? parseFloat(((item.count / total) * 100).toFixed(1)) : 0
  }));

  return {
    dimension: 'status',
    summary: {
      total,
      in_use: parseInt(inUse),
      idle: parseInt(idle),
      scrapped: parseInt(scrapped)
    },
    details
  };
}

/**
 * 按使用部门统计
 */
async function getDepartmentStatistics(where) {
  const results = await Device.findAll({
    attributes: [
      'department',
      [Device.sequelize.fn('COUNT', Device.sequelize.col('device_id')), 'count']
    ],
    where,
    group: ['department'],
    order: [[Device.sequelize.fn('COUNT', Device.sequelize.col('device_id')), 'DESC']],
    raw: true
  });

  const total = results.reduce((sum, item) => sum + parseInt(item.count), 0);

  const details = results.map(item => ({
    department: item.department,
    count: parseInt(item.count),
    percentage: total > 0 ? parseFloat(((item.count / total) * 100).toFixed(1)) : 0
  }));

  return {
    dimension: 'department',
    summary: {
      total,
      department_count: results.length
    },
    details
  };
}

/**
 * 按设备类型统计
 */
async function getTypeStatistics(where) {
  const results = await Device.findAll({
    attributes: [
      'device_type',
      [Device.sequelize.fn('COUNT', Device.sequelize.col('device_id')), 'count']
    ],
    where,
    group: ['device_type'],
    order: [[Device.sequelize.fn('COUNT', Device.sequelize.col('device_id')), 'DESC']],
    raw: true
  });

  const total = results.reduce((sum, item) => sum + parseInt(item.count), 0);

  const details = results.map(item => ({
    device_type: item.device_type,
    count: parseInt(item.count),
    percentage: total > 0 ? parseFloat(((item.count / total) * 100).toFixed(1)) : 0
  }));

  return {
    dimension: 'type',
    summary: {
      total,
      type_count: results.length
    },
    details
  };
}

/**
 * 按购买时间统计
 */
async function getTimeStatistics(where, start_date, end_date) {
  // 确定时间单位（月或年）
  let timeUnit = 'month';
  if (start_date && end_date) {
    const start = moment(start_date);
    const end = moment(end_date);
    const diffYears = end.diff(start, 'years');
    if (diffYears > 2) {
      timeUnit = 'year';
    }
  }

  const results = await Device.findAll({
    attributes: [
      [
        Device.sequelize.fn(
          'strftime',
          timeUnit === 'month' ? '%Y-%m' : '%Y',
          Device.sequelize.col('purchase_date')
        ),
        'period'
      ],
      [Device.sequelize.fn('COUNT', Device.sequelize.col('device_id')), 'count']
    ],
    where,
    group: [Device.sequelize.fn('strftime', timeUnit === 'month' ? '%Y-%m' : '%Y', Device.sequelize.col('purchase_date'))],
    order: [[Device.sequelize.fn('strftime', timeUnit === 'month' ? '%Y-%m' : '%Y', Device.sequelize.col('purchase_date')), 'ASC']],
    raw: true
  });

  const total = results.reduce((sum, item) => sum + parseInt(item.count), 0);

  const details = results.map(item => ({
    period: item.period,
    count: parseInt(item.count)
  }));

  return {
    dimension: 'time',
    time_unit: timeUnit,
    summary: {
      total
    },
    details
  };
}
