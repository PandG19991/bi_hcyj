from sqlalchemy import (Column, String, Integer, DECIMAL, DateTime, Text, 
                        ForeignKey, UniqueConstraint, Index, BIGINT,
                        PrimaryKeyConstraint, ForeignKeyConstraint)
from sqlalchemy.sql import func # 用于 server_default=func.now()
from sqlalchemy.orm import relationship

from core.db import Base # 导入在 db.py 中定义的 Base

# 注意：
# 1. 列名默认与属性名相同。
# 2. 类型映射：VARCHAR -> String, INT -> Integer, DECIMAL -> DECIMAL, DATETIME -> DateTime, TEXT -> Text.
# 3. `nullable=False` 对应 SQL 的 `NOT NULL`。
# 4. `primary_key=True` 定义主键。
# 5. `default` 和 `server_default` 用于设置默认值。
# 6. `index=True` 创建简单索引，更复杂的索引和约束在 __table_args__ 中定义。
# 7. DECIMAL 需要指定精度 (precision) 和小数位数 (scale)。
# 8. DATETIME 字段不包含时区信息，对应 MySQL 的 DATETIME 类型。应用层面需处理 UTC。

class Order(Base):
    __tablename__ = "orders"

    # 主键定义在 __table_args__ 中，因为是复合主键
    order_id = Column(String(64), nullable=False, comment='平台订单ID')
    platform = Column(String(32), nullable=False, default='xiaoe', comment='来源平台')

    user_id = Column(String(64), nullable=False, comment='平台用户ID')
    price = Column(DECIMAL(10, 2), default=0.00, comment='实付金额 (元)')
    coupon_price = Column(DECIMAL(10, 2), default=0.00, comment='优惠券抵扣 (元)')
    refund_money = Column(DECIMAL(10, 2), default=0.00, comment='退款金额 (元)')
    order_state = Column(Integer, comment='订单状态码 (小鹅通原始状态)')
    order_state_text = Column(String(100), comment='订单状态文本')
    resource_type = Column(Integer, comment='资源类型码')
    resource_type_text = Column(String(100), comment='资源类型文本')
    pay_time = Column(DateTime, comment='支付时间 (UTC)')
    created_at = Column(DateTime, nullable=False, comment='订单创建时间 (UTC)')
    updated_at = Column(DateTime, nullable=False,
                        server_default=func.now(), onupdate=func.now(),
                        comment='记录更新时间')

    # 定义与 OrderItem 的关系 (一对多)
    items = relationship("OrderItem", back_populates="order")

    # 定义表参数，包括复合主键和索引
    __table_args__ = (
        PrimaryKeyConstraint('platform', 'order_id'),
        Index('idx_user_id', 'platform', 'user_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_pay_time', 'pay_time'),
        Index('idx_updated_at', 'updated_at'),
        {'comment': '订单主表'}
    )

    def __repr__(self):
        return f"<Order(platform='{self.platform}', order_id='{self.order_id}')>"

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    order_id = Column(String(64), nullable=False, comment='平台订单ID')
    platform = Column(String(32), nullable=False, default='xiaoe', comment='来源平台')
    product_id = Column(String(64), nullable=False, comment='平台商品ID')
    product_name = Column(String(255), comment='商品名称')
    quantity = Column(Integer, default=1, comment='数量')
    price = Column(DECIMAL(10, 2), default=0.00, comment='商品单价 (元)')
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment='记录创建时间')

    # 定义与 Order 的关系 (多对一)
    # ForeignKeyConstraint 定义复合外键
    order = relationship("Order", back_populates="items")

    __table_args__ = (
        ForeignKeyConstraint(['platform', 'order_id'], ['orders.platform', 'orders.order_id']),
        UniqueConstraint('platform', 'order_id', 'product_id', name='uk_order_product'),
        Index('idx_order_id', 'platform', 'order_id'),
        Index('idx_product_id', 'platform', 'product_id'),
        {'comment': '订单商品明细表'}
    )

    def __repr__(self):
        return f"<OrderItem(order_id='{self.order_id}', product_id='{self.product_id}')>"

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), nullable=False, comment='平台用户ID')
    platform = Column(String(32), nullable=False, default='xiaoe', comment='来源平台')

    nickname = Column(String(255), comment='用户昵称')
    avatar = Column(String(512), comment='用户头像 URL')
    mobile = Column(String(32), comment='手机号 (脱敏或加密存储)', index=True) # 添加索引
    register_time = Column(DateTime, comment='注册时间 (UTC)')
    updated_at = Column(DateTime, nullable=False,
                        server_default=func.now(), onupdate=func.now(),
                        comment='记录更新时间')

    __table_args__ = (
        PrimaryKeyConstraint('platform', 'user_id'),
        # Index('idx_mobile', 'platform', 'mobile'), # 在列定义中添加了 index=True
        {'comment': '用户表'}
    )

    def __repr__(self):
        return f"<User(platform='{self.platform}', user_id='{self.user_id}')>"

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(64), nullable=False, comment='平台商品ID')
    platform = Column(String(32), nullable=False, default='xiaoe', comment='来源平台')

    title = Column(String(255), comment='商品标题')
    price = Column(DECIMAL(10, 2), default=0.00, comment='商品标价 (元)')
    type = Column('type', Integer, comment='商品类型码 (小鹅通原始类型)') # 使用 'type' 避免与 Python 关键字冲突
    cover_img = Column(String(512), comment='封面图 URL')
    status = Column(Integer, comment='商品状态码')
    created_at = Column(DateTime, comment='商品创建时间 (UTC)', index=True)
    updated_at = Column(DateTime, nullable=False,
                        server_default=func.now(), onupdate=func.now(),
                        comment='记录更新时间')

    __table_args__ = (
        PrimaryKeyConstraint('platform', 'product_id'),
        # Index('idx_created_at', 'created_at'), # 在列定义中添加了 index=True
        {'comment': '商品表'}
    )

    def __repr__(self):
        return f"<Product(platform='{self.platform}', product_id='{self.product_id}')>"

class SyncStatus(Base):
    __tablename__ = "sync_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(32), nullable=False, default='xiaoe', comment='来源平台')
    data_type = Column(String(32), nullable=False, comment='数据类型 (e.g., order, user, product)')
    sync_mode = Column(String(16), nullable=False, comment='同步模式 (e.g., incremental, full, status_update)')
    last_sync_timestamp = Column(DateTime, comment='上次成功同步到的时间点 (用于增量)')
    last_run_start_time = Column(DateTime, comment='上次任务开始时间')
    last_run_end_time = Column(DateTime, comment='上次任务结束时间')
    status = Column(String(16), comment='上次任务状态 (success, failed)')
    message = Column(Text, comment='状态信息或错误消息')

    __table_args__ = (
        UniqueConstraint('platform', 'data_type', 'sync_mode', name='uk_platform_datatype_mode'),
        {'comment': '数据同步状态跟踪表'}
    )

    def __repr__(self):
        return f"<SyncStatus(platform='{self.platform}', data_type='{self.data_type}', mode='{self.sync_mode}')>"

# 可选：创建所有定义的表 (通常在应用启动或单独的脚本中执行)
# from core.db import engine
# def create_tables():
#     logger.info("Creating database tables...")
#     Base.metadata.create_all(bind=engine)
#     logger.info("Database tables created (if they didn't exist).")
#
# if __name__ == '__main__':
#     create_tables() # 谨慎：直接运行会尝试创建表 