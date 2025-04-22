# 数据库 Schema (MVP)

本文件定义了项目 MVP 阶段所需的核心数据库表结构。

**数据库类型:** MySQL 8.0+
**字符集:** `utf8mb4`

## 1. `orders` (订单主表)

存储小鹅通订单的核心信息。

```sql
CREATE TABLE orders (
    order_id VARCHAR(64) NOT NULL COMMENT '平台订单ID',
    platform VARCHAR(32) NOT NULL DEFAULT 'xiaoe' COMMENT '来源平台',
    user_id VARCHAR(64) NOT NULL COMMENT '平台用户ID',
    price DECIMAL(10, 2) DEFAULT 0.00 COMMENT '实付金额 (元)',
    coupon_price DECIMAL(10, 2) DEFAULT 0.00 COMMENT '优惠券抵扣 (元)',
    refund_money DECIMAL(10, 2) DEFAULT 0.00 COMMENT '退款金额 (元)',
    order_state INT COMMENT '订单状态码 (小鹅通原始状态)',
    order_state_text VARCHAR(100) COMMENT '订单状态文本',
    resource_type INT COMMENT '资源类型码',
    resource_type_text VARCHAR(50) COMMENT '资源类型文本 (e.g., \'知识商品\', \'实物商品\')',
    pay_time DATETIME COMMENT '支付时间 (UTC)',
    aftersale_id VARCHAR(100) COMMENT '售后单号 (如果订单发生售后)',
    created_at DATETIME NOT NULL COMMENT '订单创建时间 (UTC)',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    -- 根据需要添加更多核心字段, 例如 ship_state, pay_way 等
    PRIMARY KEY (platform, order_id),
    INDEX idx_user_id (platform, user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_pay_time (pay_time),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单主表';
```

## 2. `order_items` (订单商品表)

存储订单包含的商品信息。

```sql
CREATE TABLE order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL COMMENT '平台订单ID',
    platform VARCHAR(32) NOT NULL DEFAULT 'xiaoe' COMMENT '来源平台',
    product_id VARCHAR(64) NOT NULL COMMENT '平台商品ID',
    product_name VARCHAR(255) COMMENT '商品名称',
    quantity INT DEFAULT 1 COMMENT '数量',
    price DECIMAL(10, 2) DEFAULT 0.00 COMMENT '商品单价 (元)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    -- 确保与 orders 表的外键关系 (逻辑上或物理上)
    UNIQUE KEY uk_order_product (platform, order_id, product_id),
    INDEX idx_order_id (platform, order_id),
    INDEX idx_product_id (platform, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单商品明细表';
```

## 3. `users` (用户表)

存储小鹅通用户的核心信息。

```sql
CREATE TABLE users (
    user_id VARCHAR(64) NOT NULL COMMENT '平台用户ID',
    platform VARCHAR(32) NOT NULL DEFAULT 'xiaoe' COMMENT '来源平台',
    nickname VARCHAR(255) COMMENT '用户昵称',
    avatar VARCHAR(512) COMMENT '用户头像 URL',
    mobile VARCHAR(32) COMMENT '手机号 (脱敏或加密存储)',
    register_time DATETIME COMMENT '注册时间 (UTC)',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    -- 根据需要添加 email, gender 等核心字段
    PRIMARY KEY (platform, user_id),
    INDEX idx_mobile (platform, mobile)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

## 4. `products` (商品表)

存储小鹅通商品的核心信息。

```sql
CREATE TABLE products (
    product_id VARCHAR(64) NOT NULL COMMENT '平台商品ID',
    platform VARCHAR(32) NOT NULL DEFAULT 'xiaoe' COMMENT '来源平台',
    title VARCHAR(255) COMMENT '商品标题',
    price DECIMAL(10, 2) DEFAULT 0.00 COMMENT '商品标价 (元)',
    `type` INT COMMENT '商品类型码 (小鹅通原始类型)',
    cover_img VARCHAR(512) COMMENT '封面图 URL',
    status INT COMMENT '商品状态码',
    created_at DATETIME COMMENT '商品创建时间 (UTC)',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    PRIMARY KEY (platform, product_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

```

## 5. `sync_status` (同步状态表)

用于跟踪不同数据类型的同步进度。

```sql
CREATE TABLE sync_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(32) NOT NULL DEFAULT 'xiaoe' COMMENT '来源平台',
    data_type VARCHAR(32) NOT NULL COMMENT '数据类型 (e.g., order, user, product)',
    sync_mode VARCHAR(16) NOT NULL COMMENT '同步模式 (e.g., incremental, full, status_update)',
    last_sync_timestamp DATETIME COMMENT '上次成功同步到的时间点 (用于增量)',
    last_run_start_time DATETIME COMMENT '上次任务开始时间',
    last_run_end_time DATETIME COMMENT '上次任务结束时间',
    status VARCHAR(16) COMMENT '上次任务状态 (success, failed)',
    message TEXT COMMENT '状态信息或错误消息',
    UNIQUE KEY uk_platform_datatype_mode (platform, data_type, sync_mode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据同步状态跟踪表';
```

**注意:**

*   所有 `DATETIME` 字段建议存储 **UTC** 时间，便于处理时区问题。在应用层面进行转换。
*   对于敏感信息（如手机号），考虑进行脱敏或加密处理。
*   以上仅为核心字段，可根据实际业务需求增减。
*   索引的创建需要根据实际查询场景进行优化。