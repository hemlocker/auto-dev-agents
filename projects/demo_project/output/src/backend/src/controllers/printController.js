const Device = require('../../models/Device');
const QRCode = require('qrcode');
const PDFDocument = require('pdfkit');

/**
 * 获取设备标签数据（包含二维码）
 */
exports.getLabelData = async (req, res) => {
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

    // 生成二维码（包含设备详情 URL）
    const qrCodeUrl = `http://localhost:3000/device/detail/${device.device_id}`;
    const qrCodeDataUri = await QRCode.toDataURL(qrCodeUrl, {
      width: 200,
      margin: 2,
      errorCorrectionLevel: 'M'
    });

    res.json({
      code: 200,
      message: 'success',
      data: {
        device_id: device.device_id,
        device_name: device.device_name,
        device_type: device.device_type,
        specification: device.specification,
        purchase_date: device.purchase_date,
        department: device.department,
        user_name: device.user_name,
        status: device.status,
        location: device.location,
        remark: device.remark,
        qr_code: qrCodeDataUri
      }
    });
  } catch (error) {
    console.error('获取标签数据失败:', error);
    res.status(500).json({
      code: 500,
      message: '获取标签数据失败',
      data: null
    });
  }
};

/**
 * 批量打印设备标签（生成 PDF）
 */
exports.printBatchLabels = async (req, res) => {
  try {
    const { device_ids } = req.body;
    
    if (!device_ids || !Array.isArray(device_ids) || device_ids.length === 0) {
      return res.status(400).json({
        code: 400,
        message: '请提供设备 ID 列表',
        data: null
      });
    }

    // 查询设备信息
    const devices = await Device.findAll({
      where: {
        device_id: device_ids
      }
    });

    if (devices.length === 0) {
      return res.status(404).json({
        code: 404,
        message: '未找到设备信息',
        data: null
      });
    }

    // 创建 PDF 文档
    const doc = new PDFDocument({
      size: 'A4',
      margins: {
        top: 20,
        bottom: 20,
        left: 20,
        right: 20
      }
    });

    // 设置响应头
    res.setHeader('Content-Type', 'application/pdf');
    const timestamp = new Date().getTime();
    res.setHeader('Content-Disposition', `attachment; filename="设备标签_${timestamp}.pdf"`);

    // 将 PDF 输出到响应
    doc.pipe(res);

    // 标签尺寸（毫米转点）
    const labelWidth = 255; // 90mm ≈ 255 points
    const labelHeight = 170; // 60mm ≈ 170 points
    const labelsPerRow = 2;
    const labelsPerCol = 4;
    const gapX = 20;
    const gapY = 20;

    // 生成每个设备的标签
    for (let i = 0; i < devices.length; i++) {
      const device = devices[i];
      
      // 计算位置
      const row = Math.floor(i / labelsPerRow) % labelsPerCol;
      const col = i % labelsPerRow;
      const pageIndex = Math.floor(i / (labelsPerRow * labelsPerCol));

      // 如果是新页面，添加页码
      if (i % (labelsPerRow * labelsPerCol) === 0) {
        if (i > 0) {
          doc.addPage();
        }
      }

      const x = 20 + col * (labelWidth + gapX);
      const y = 20 + row * (labelHeight + gapY);

      // 绘制标签边框
      doc.rect(x, y, labelWidth, labelHeight).stroke('#000');

      // 标题
      doc.fontSize(14).font('Helvetica-Bold').text('设备标签', x + 10, y + 10, {
        width: labelWidth - 20,
        align: 'center'
      });

      // 分隔线
      doc.moveTo(x + 10, y + 35).lineTo(x + labelWidth - 10, y + 35).stroke('#000');

      // 设备信息
      const startY = y + 45;
      const lineHeight = 18;
      const fontSize = 10;
      
      doc.fontSize(fontSize).font('Helvetica');
      
      const info = [
        `设备编号：${device.device_id}`,
        `设备名称：${device.device_name}`,
        `设备类型：${device.device_type}`,
        `规格型号：${device.specification || ''}`,
        `使用部门：${device.department}`,
        `使用人：${device.user_name}`,
        `购买日期：${device.purchase_date}`,
        `设备状态：${device.status}`
      ];

      info.forEach((text, index) => {
        doc.text(text, x + 10, startY + index * lineHeight, {
          width: labelWidth - 120,
          align: 'left'
        });
      });

      // 生成并添加二维码
      const qrCodeUrl = `http://localhost:3000/device/detail/${device.device_id}`;
      const qrCodeImage = await QRCode.toDataURL(qrCodeUrl, {
        width: 200,
        margin: 1,
        errorCorrectionLevel: 'M'
      });

      // 解码 base64 并添加到 PDF
      const base64Data = qrCodeImage.replace(/^data:image\/png;base64,/, '');
      const imageBuffer = Buffer.from(base64Data, 'base64');
      
      const qrSize = 80;
      const qrX = x + labelWidth - 100;
      const qrY = startY + info.length * lineHeight - 10;
      
      doc.image(imageBuffer, qrX, qrY, {
        width: qrSize,
        height: qrSize
      });
    }

    // 结束 PDF 文档
    doc.end();
  } catch (error) {
    console.error('批量打印失败:', error);
    if (!res.headersSent) {
      res.status(500).json({
        code: 500,
        message: '批量打印失败',
        data: null
      });
    }
  }
};
