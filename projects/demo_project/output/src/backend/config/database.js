const { Sequelize } = require('sequelize');
const path = require('path');

// 数据库配置
const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: path.join(__dirname, '../../database/device.db'),
  logging: false
});

// 测试连接
sequelize.authenticate()
  .then(() => {
    console.log('数据库连接成功');
  })
  .catch(err => {
    console.error('数据库连接失败:', err);
  });

module.exports = sequelize;
