const Device = require('../../models/Device');
const { Op } = require('sequelize');
const XLSX = require('xlsx');
const moment = require('moment');

/**
 * 导出设备数据
 */
exports.exportDevices = async (req, res) => {
  try {
    const { keyword, device_type, status, department } = req.query;
    
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
    
    // 查询所有符合条件的设备
    const devices = await Device.findAll({
      where,
      order: [['device_id', 'ASC']]
    });

    // 准备导出数据
    const exportData = [
      ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注']
    ];

    devices.forEach(device => {
      exportData.push([
        device.device_id,
        device.device_name,
        device.device_type,
        device.specification || '',
        device.purchase_date,
        device.department,
        device.user_name,
        device.status,
        device.location || '',
        device.remark || ''
      ]);
    });

    // 创建工作簿
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(exportData);

    // 设置列宽
    ws['!cols'] = [
      { wch: 15 }, // 设备编号
      { wch: 25 }, // 设备名称
      { wch: 15 }, // 设备类型
      { wch: 25 }, // 规格型号
      { wch: 15 }, // 购买日期
      { wch: 15 }, // 使用部门
      { wch: 12 }, // 使用人
      { wch: 12 }, // 设备状态
      { wch: 20 }, // 存放位置
      { wch: 30 }  // 备注
    ];

    XLSX.utils.book_append_sheet(wb, ws, '设备列表');

    // 生成文件名
    const timestamp = moment().format('YYYYMMDD_HHmmss');
    const filename = `设备列表_${timestamp}.xlsx`;

    // 设置响应头
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', `attachment; filename="${encodeURIComponent(filename)}"`);

    // 发送文件
    XLSX.write(wb, res, { type: 'node', bookType: 'xlsx' });
  } catch (error) {
    console.error('导出失败:', error);
    res.status(500).json({
      code: 500,
      message: '导出失败',
      data: null
    });
  }
};
