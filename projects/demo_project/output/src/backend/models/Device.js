const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Device = sequelize.define('Device', {
  device_id: {
    type: DataTypes.STRING(50),
    primaryKey: true,
    allowNull: false
  },
  device_name: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  device_type: {
    type: DataTypes.STRING(50),
    allowNull: false
  },
  specification: {
    type: DataTypes.STRING(200),
    allowNull: true
  },
  purchase_date: {
    type: DataTypes.DATEONLY,
    allowNull: false
  },
  department: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  user_name: {
    type: DataTypes.STRING(50),
    allowNull: false
  },
  status: {
    type: DataTypes.STRING(20),
    allowNull: false,
    defaultValue: '闲置'
  },
  location: {
    type: DataTypes.STRING(200),
    allowNull: true
  },
  remark: {
    type: DataTypes.TEXT,
    allowNull: true
  }
}, {
  tableName: 'devices',
  timestamps: false
});

module.exports = Device;
