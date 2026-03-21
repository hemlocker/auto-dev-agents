-- 设备管理系统数据库初始化脚本
-- SQLite 建表语句

CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    specification VARCHAR(200),
    purchase_date DATE NOT NULL,
    department VARCHAR(100) NOT NULL,
    user_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT '闲置',
    location VARCHAR(200),
    remark TEXT
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_device_type ON devices(device_type);
CREATE INDEX IF NOT EXISTS idx_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_department ON devices(department);
CREATE INDEX IF NOT EXISTS idx_user_name ON devices(user_name);
