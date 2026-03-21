const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const sequelize = require('../config/database');
const deviceRoutes = require('./routes/deviceRoutes');
const deviceTypeRoutes = require('./routes/deviceTypeRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// 静态文件服务（前端）
app.use(express.static(path.join(__dirname, '../../frontend/dist')));

// API 路由
app.use('/api', deviceRoutes);
app.use('/api', deviceTypeRoutes);

// 前端路由 - 所有非 API 请求返回前端页面
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../../frontend/dist/index.html'));
});

// 全局错误处理
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    code: 500,
    message: '服务器内部错误',
    data: null
  });
});

// 初始化数据库并启动服务
const startServer = async () => {
  try {
    // 同步数据库模型
    await sequelize.sync();
    console.log('数据库同步成功');
    
    // 启动服务器
    app.listen(PORT, () => {
      console.log(`服务器运行在 http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('启动失败:', error);
    process.exit(1);
  }
};

startServer();

module.exports = app;
