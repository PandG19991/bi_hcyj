-- 小鹅通数据同步数据库表结构

-- 创建订单表
CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(32) UNIQUE NOT NULL,
    user_id VARCHAR(32) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    coupon_price DECIMAL(10,2) DEFAULT 0,
    refund_money DECIMAL(10,2) DEFAULT 0,
    order_state INT NOT NULL,
    order_state_text VARCHAR(32),
    resource_type INT,
    resource_type_text VARCHAR(32),
    ship_state INT DEFAULT 0,
    ship_state_text VARCHAR(32),
    pay_way INT,
    client_type INT,
    collection_way INT,
    after_sales_state INT DEFAULT 0,
    team_buy_state INT DEFAULT 0,
    sales_state INT DEFAULT 0,
    created_at DATETIME,
    pay_time DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小鹅通订单表';

-- 创建订单商品表
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(32) NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小鹅通订单商品表';

-- 创建用户表
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(32) UNIQUE NOT NULL,
    nickname VARCHAR(64),
    avatar VARCHAR(255),
    mobile VARCHAR(20),
    email VARCHAR(64),
    gender INT DEFAULT 0,
    birthday VARCHAR(32),
    province VARCHAR(32),
    city VARCHAR(32),
    register_time DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_mobile (mobile),
    INDEX idx_register_time (register_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小鹅通用户表';

-- 创建商品表
CREATE TABLE products (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id VARCHAR(32) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    sub_title VARCHAR(255),
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    type INT,
    cover_img VARCHAR(255),
    status INT,
    created_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='小鹅通商品表';

-- 创建同步任务表
CREATE TABLE sync_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_type VARCHAR(32) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status VARCHAR(16) NOT NULL,
    records_count INT DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_type (task_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='同步任务记录表';

-- 创建日志表
CREATE TABLE sync_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT,
    log_level VARCHAR(16) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_log_level (log_level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='同步日志表'; 