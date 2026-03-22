const Device = require('../../models/Device');
const { Op } = require('sequelize');
const XLSX = require('xlsx');
const moment = require('moment');

/**
 * 生成导入模板
 */
exports.downloadTemplate = async (req, res) => {
  try {
    // 创建模板数据
    const templateData = [
      ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
      ['DEV001', '联想 ThinkPad X1', '电脑', 'i7/16G/512G', '2025-01-15', '技术部', '张三', '在用', 'A 栋 301', '示例数据'],
      ['DEV002', '惠普打印机', '打印机', 'LaserJet Pro', '2025-03-20', '行政部', '李四', '闲置', 'B 栋 102', '新采购']
    ];

    // 创建工作簿
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(templateData);

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

    XLSX.utils.book_append_sheet(wb, ws, '设备导入模板');

    // 设置响应头
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="设备导入模板.xlsx"');

    // 发送文件
    XLSX.write(wb, res, { type: 'node', bookType: 'xlsx' });
  } catch (error) {
    console.error('生成模板失败:', error);
    res.status(500).json({
      code: 500,
      message: '生成模板失败',
      data: null
    });
  }
};

/**
 * 验证单行数据
 */
function validateRow(row, rowNum) {
  const errors = [];
  
  // 设备编号验证
  if (!row['设备编号'] || String(row['设备编号']).trim() === '') {
    errors.push('设备编号不能为空');
  } else if (String(row['设备编号']).length > 50) {
    errors.push('设备编号不能超过 50 个字符');
  } else if (!/^[\w\-]+$/.test(String(row['设备编号']))) {
    errors.push('设备编号只能包含字母、数字、下划线、中划线');
  }

  // 设备名称验证
  if (!row['设备名称'] || String(row['设备名称']).trim() === '') {
    errors.push('设备名称不能为空');
  } else if (String(row['设备名称']).length > 100) {
    errors.push('设备名称不能超过 100 个字符');
  }

  // 设备类型验证
  if (!row['设备类型'] || String(row['设备类型']).trim() === '') {
    errors.push('设备类型不能为空');
  }

  // 购买日期验证
  if (!row['购买日期']) {
    errors.push('购买日期不能为空');
  } else {
    const date = moment(row['购买日期'], 'YYYY-MM-DD', true);
    if (!date.isValid()) {
      errors.push('购买日期格式不正确，应为 YYYY-MM-DD');
    } else if (date.isAfter(moment(), 'day')) {
      errors.push('购买日期不能晚于当前日期');
    }
  }

  // 使用部门验证
  if (!row['使用部门'] || String(row['使用部门']).trim() === '') {
    errors.push('使用部门不能为空');
  } else if (String(row['使用部门']).length > 100) {
    errors.push('使用部门不能超过 100 个字符');
  }

  // 使用人验证
  if (!row['使用人'] || String(row['使用人']).trim() === '') {
    errors.push('使用人不能为空');
  } else if (String(row['使用人']).length > 50) {
    errors.push('使用人不能超过 50 个字符');
  }

  // 设备状态验证
  if (!row['设备状态']) {
    errors.push('设备状态不能为空');
  } else if (!['在用', '闲置', '报废'].includes(String(row['设备状态']))) {
    errors.push('设备状态必须是在用、闲置或报废');
  }

  // 存放位置验证（可选）
  if (row['存放位置'] && String(row['存放位置']).length > 200) {
    errors.push('存放位置不能超过 200 个字符');
  }

  // 备注验证（可选）
  if (row['备注'] && String(row['备注']).length > 500) {
    errors.push('备注不能超过 500 个字符');
  }

  return errors;
}

/**
 * 批量导入设备
 */
exports.importDevices = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        code: 400,
        message: '请上传 Excel 文件',
        data: null
      });
    }

    // 读取 Excel 文件
    const workbook = XLSX.read(req.file.buffer, { type: 'buffer' });
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    
    // 转换为 JSON
    const jsonData = XLSX.utils.sheet_to_json(worksheet);

    if (jsonData.length === 0) {
      return res.status(400).json({
        code: 400,
        message: 'Excel 文件为空',
        data: null
      });
    }

    const results = {
      total: jsonData.length,
      success: 0,
      failed: 0,
      errors: []
    };

    // 批量处理设备数据
    for (let i = 0; i < jsonData.length; i++) {
      const row = jsonData[i];
      const rowNum = i + 2; // Excel 行号（从 1 开始，第一行是表头）

      // 验证数据
      const validationErrors = validateRow(row, rowNum);
      
      if (validationErrors.length > 0) {
        results.failed++;
        results.errors.push({
          row: rowNum,
          device_id: row['设备编号'] || '',
          reason: validationErrors.join('; ')
        });
        continue;
      }

      // 检查设备编号是否已存在
      const existing = await Device.findByPk(String(row['设备编号']));
      if (existing) {
        results.failed++;
        results.errors.push({
          row: rowNum,
          device_id: row['设备编号'],
          reason: '设备编号已存在'
        });
        continue;
      }

      // 创建设备记录
      try {
        await Device.create({
          device_id: String(row['设备编号']),
          device_name: String(row['设备名称']),
          device_type: String(row['设备类型']),
          specification: row['规格型号'] ? String(row['规格型号']) : null,
          purchase_date: moment(row['购买日期']).format('YYYY-MM-DD'),
          department: String(row['使用部门']),
          user_name: String(row['使用人']),
          status: String(row['设备状态']),
          location: row['存放位置'] ? String(row['存放位置']) : null,
          remark: row['备注'] ? String(row['备注']) : null
        });
        results.success++;
      } catch (error) {
        results.failed++;
        results.errors.push({
          row: rowNum,
          device_id: row['设备编号'] || '',
          reason: error.message
        });
      }
    }

    res.json({
      code: 200,
      message: '导入完成',
      data: results
    });
  } catch (error) {
    console.error('导入失败:', error);
    res.status(500).json({
      code: 500,
      message: '导入失败',
      data: null
    });
  }
};
