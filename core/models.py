from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Text,
    DECIMAL, JSON, Index, Boolean, BigInteger, SmallInteger, func,
    ForeignKeyConstraint, UniqueConstraint, PrimaryKeyConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from typing import List, Optional
import datetime

# 从 core.db 导入共享的 Base
from .db import Base

class SyncStatus(Base):
    __tablename__ = 'sync_status'

    # 使用 sync_target 作为主键更合适，区分不同的同步任务
    sync_target = Column(String(100), primary_key=True, comment='同步目标标识 (例如: xiaoe_orders_incremental, xiaoe_aftersales_full)')
    # last_sync_time 存储查询用的时间戳
    last_sync_time = Column(DateTime, nullable=True, comment='上次成功同步的查询截止时间 (基于查询条件)')
    # last_sync_id 可选，用于某些接口的游标
    last_sync_id = Column(String(100), nullable=True, comment='上次成功同步的最后一个记录ID (如果适用)')
    # sync_cursor 作为通用的分页/增量标记
    sync_cursor = Column(String(255), nullable=True, comment='用于分页或增量同步的游标 (如 page_index, next_cursor)')
    last_successful_run_start = Column(DateTime, nullable=True, comment='最后一次成功执行脚本的开始时间')
    last_successful_run_end = Column(DateTime, nullable=True, comment='最后一次成功执行脚本的结束时间')
    status = Column(String(20), default='pending', comment='最后一次运行状态 (success, failed, pending)')
    message = Column(Text, nullable=True, comment='最后一次运行的消息或错误')
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='此记录的最后更新时间')


    def __repr__(self):
        return f"<SyncStatus(sync_target='{self.sync_target}', last_sync_time='{self.last_sync_time}', status='{self.status}')>"

class User(Base):
    __tablename__ = 'users'

    # 使用平台 user_id 和 platform 作为复合主键
    user_id = Column(String(100, collation='utf8mb4_unicode_ci'), primary_key=True, comment='平台用户ID (如: u_xxxxx)')
    platform = Column(String(32, collation='utf8mb4_unicode_ci'), primary_key=True, default='xiaoe', comment='来源平台')

    nickname = Column(String(255), nullable=True, comment='用户昵称')
    avatar = Column(String(500), nullable=True, comment='用户头像URL')
    phone = Column(String(50), nullable=True, index=True, comment='用户手机号 (可能脱敏)') # 索引方便查询
    register_time = Column(DateTime, nullable=True, comment='平台注册时间 (如果API提供)')

    # 系统时间戳
    first_seen_at = Column(DateTime, default=func.now(), comment='在本系统中首次记录的时间')
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='在本系统的最后更新时间')

    # 关系 (假设一个用户可以有多个平台的订单和售后)
    # orders = relationship("Order", back_populates="user", foreign_keys="[Order.user_id, Order.platform]") # 需要显式指定外键
    # aftersale_orders = relationship("AftersaleOrder", back_populates="user", foreign_keys="[AftersaleOrder.user_id, AftersaleOrder.platform]")

    __table_args__ = (
        Index('ix_users_phone', 'platform', 'phone'), # 复合索引
        {'comment': '用户基础信息表'}
    )


    def __repr__(self):
        return f"<User(platform='{self.platform}', user_id='{self.user_id}', nickname='{self.nickname}')>"

class Product(Base):
    __tablename__ = 'products'

    # 使用平台 product_id 和 platform 作为复合主键
    product_id = Column(String(100, collation='utf8mb4_unicode_ci'), primary_key=True, comment='平台商品ID/SPUID (如: i_xxxxx, p_xxxxx)')
    platform = Column(String(32, collation='utf8mb4_unicode_ci'), primary_key=True, default='xiaoe', comment='来源平台')

    name = Column(String(500), nullable=True, comment='商品名称') # 原 title
    type = Column(Integer, nullable=True, comment='商品类型代码 (来自 API, resource_type)')
    # type_desc 存储 API 返回的 spu_type 字符串
    type_desc = Column(String(100), nullable=True, comment='商品类型描述 (来自 API, spu_type)')
    img_url = Column(String(500), nullable=True, comment='商品主图URL (来自 goods_img[0])') # 原 cover_img

    # 新增字段以匹配 get_goods_relations API
    price_low = Column(DECIMAL(10, 2), nullable=True, comment='最低价格 (元)')
    price_high = Column(DECIMAL(10, 2), nullable=True, comment='最高价格 (元)')
    status = Column(Integer, nullable=True, comment='上架状态 (来自 sale_status, 0-下架/待上架, 1-已上架)')
    created_at_platform = Column(DateTime, nullable=True, comment='商品创建时间 (平台时间)')
    updated_at_platform = Column(DateTime, nullable=True, comment='商品更新时间 (平台时间)')

    # 系统时间戳
    first_seen_at = Column(DateTime, default=func.now(), comment='在本系统中首次记录的时间')
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='在本系统的最后更新时间')

    # 关系 (一个商品可以出现在多个订单项中)
    # order_items = relationship("OrderItem", back_populates="product", foreign_keys="[OrderItem.product_id, OrderItem.platform]")


    __table_args__ = (
        Index('ix_products_created_at', 'platform', 'created_at_platform'), # 添加索引
        Index('ix_products_updated_at', 'platform', 'updated_at_platform'), # 添加索引
        {'comment': '商品基础信息表'}
    )

    def __repr__(self):
        return f"<Product(platform='{self.platform}', product_id='{self.product_id}', name='{self.name}')>"


class Order(Base):
    __tablename__ = 'orders'

    # 使用平台 order_id 和 platform 作为复合主键
    order_id = Column(String(100, collation='utf8mb4_unicode_ci'), primary_key=True, comment='平台订单ID')
    platform = Column(String(32, collation='utf8mb4_unicode_ci'), primary_key=True, default='xiaoe', comment='来源平台')

    app_id = Column(String(100), nullable=True, comment='店铺ID (冗余)')
    user_id = Column(String(100, collation='utf8mb4_unicode_ci'), nullable=False, index=True, comment='平台用户ID') # 加索引方便按用户查询

    # 订单状态与类型
    order_state = Column(SmallInteger, nullable=True, index=True, comment='订单状态码')
    pay_state = Column(SmallInteger, nullable=True, index=True, comment='支付状态码')
    order_type = Column(SmallInteger, nullable=True, comment='订单类型码')
    sub_order_type = Column(SmallInteger, nullable=True, comment='子订单类型码')
    aftersale_show_state = Column(SmallInteger, nullable=True, comment='售后显示状态码')
    settle_state = Column(SmallInteger, nullable=True, comment='结算状态码')
    check_state = Column(SmallInteger, nullable=True, comment='核销状态码')
    order_close_type = Column(SmallInteger, nullable=True, comment='订单关闭类型码')
    is_deleted = Column(Boolean, nullable=True, comment='是否删除')

    # 价格相关 (统一使用Decimal存储元，精度10,2)
    actual_fee = Column(DECIMAL(10, 2), nullable=True, comment='订单实付金额 (元)')
    goods_original_total_price = Column(DECIMAL(10, 2), nullable=True, comment='商品原始总价 (元)')
    discount_amount = Column(DECIMAL(10, 2), nullable=True, comment='订单优惠金额 (元)')
    freight_actual_price = Column(DECIMAL(10, 2), nullable=True, comment='运费实付金额 (元)')
    freight_original_price = Column(DECIMAL(10, 2), nullable=True, comment='运费原始金额 (元)')
    modified_amount = Column(DECIMAL(10, 2), nullable=True, comment='改价金额 (元)')
    deduct_amount = Column(DECIMAL(10, 2), nullable=True, comment='抵扣金额 (元)')
    refund_fee = Column(DECIMAL(10, 2), nullable=True, comment='退款金额 (元)')

    # 时间相关
    created_at_platform = Column(DateTime, nullable=True, index=True, comment='订单创建时间 (平台时间)')
    pay_state_time = Column(DateTime, nullable=True, index=True, comment='支付时间 (平台时间)')
    order_state_time = Column(DateTime, nullable=True, comment='订单状态更新时间 (平台时间)')
    aftersale_show_state_time = Column(DateTime, nullable=True, comment='售后状态更新时间 (平台时间)')
    settle_state_time = Column(DateTime, nullable=True, comment='结算状态更新时间 (平台时间)')
    refund_time = Column(DateTime, nullable=True, comment='退款时间 (平台时间)')
    update_time_platform = Column(DateTime, nullable=True, index=True, comment='订单更新时间 (平台时间, 来自v2.0)') # 原 update_time

    # 商品概览 (冗余信息，方便查询)
    goods_buy_num = Column(Integer, nullable=True, comment='商品购买总数')
    goods_name_overview = Column(Text, nullable=True, comment='商品名称概览 (可能含多个)')
    goods_spu_type = Column(SmallInteger, nullable=True, comment='商品一级类型码')
    goods_spu_sub_type = Column(String(100), nullable=True, comment='商品二级类型')

    # 渠道与来源
    channel_type = Column(SmallInteger, nullable=True, comment='渠道类型码')
    channel_bus_id = Column(String(100), nullable=True, comment='渠道业务ID')
    source = Column(SmallInteger, nullable=True, comment='下单终端类型码')
    wx_app_type = Column(SmallInteger, nullable=True, comment='微信应用类型码')

    # 关联信息
    relation_order_type = Column(SmallInteger, nullable=True, comment='关联订单类型码')
    relation_order_id = Column(String(100), nullable=True, comment='关联订单ID')
    relation_order_appid = Column(String(100), nullable=True, comment='关联订单店铺ID')

    # 支付信息
    pay_type = Column(SmallInteger, nullable=True, comment='支付方式码')
    out_order_id_payment = Column(String(100), nullable=True, comment='商户订单号 (来自payment_info)')
    third_order_id = Column(String(100), nullable=True, comment='第三方支付订单号')
    trade_id = Column(String(100), nullable=True, comment='交易ID')

    # 分销/活动信息
    share_type = Column(SmallInteger, nullable=True, comment='分享类型码')
    share_user_id = Column(String(100), nullable=True, comment='分享者用户ID')
    distribute_type_bitmap = Column(JSON, nullable=True, comment='分销类型位图 (JSON存储)')
    activity_type_bitmap = Column(JSON, nullable=True, comment='活动类型位图 (JSON存储)')

    # 物流相关
    ship_way_choose_type = Column(SmallInteger, nullable=True, comment='配送方式选择类型码')
    ship_info = Column(JSON, nullable=True, comment='物流信息 (JSON存储, 含地址/物流公司/单号等)') # 包含v1/v2的地址和物流信息

    # 备注信息
    user_comment = Column(Text, nullable=True, comment='用户留言')
    merchant_remark = Column(Text, nullable=True, comment='商家备注')

    # 其他
    use_collection = Column(SmallInteger, nullable=True, comment='是否使用信息采集')

    # 系统字段
    first_seen_at = Column(DateTime, default=func.now(), comment='在本系统中首次记录的时间')
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='在本系统的最后更新时间')

    # 关系 (一对多)
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan",
                               primaryjoin="and_(Order.order_id==foreign(OrderItem.order_id), Order.platform==foreign(OrderItem.platform))")
    aftersale_orders = relationship("AftersaleOrder", back_populates="order",
                                   primaryjoin="and_(Order.order_id==foreign(AftersaleOrder.order_id), Order.platform==foreign(AftersaleOrder.platform))")

    # 复合外键到 User
    # user = relationship("User", back_populates="orders", foreign_keys=[user_id, platform])

    __table_args__ = (
        ForeignKeyConstraint(['platform', 'user_id'], ['users.platform', 'users.user_id']),
        Index('ix_orders_user_id_created_at', 'platform', 'user_id', 'created_at_platform'),
        Index('ix_orders_created_at', 'platform', 'created_at_platform'), # 按平台和创建时间索引
        Index('ix_orders_pay_state_time', 'platform', 'pay_state_time'),   # 按平台和支付时间索引
        Index('ix_orders_update_time', 'platform', 'update_time_platform'), # 按平台和更新时间索引
        {'comment': '订单主表'}
    )

    def __repr__(self):
        return f"<Order(platform='{self.platform}', order_id='{self.order_id}')>"

class OrderItem(Base):
    __tablename__ = 'order_items'

    # 使用自增ID作为主键
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 复合外键关联到 Order 表
    order_id = Column(String(100, collation='utf8mb4_unicode_ci'), nullable=False, comment='平台订单ID')
    platform = Column(String(32, collation='utf8mb4_unicode_ci'), nullable=False, default='xiaoe', comment='来源平台')
    # 复合外键关联到 Product 表
    product_id = Column(String(100, collation='utf8mb4_unicode_ci'), nullable=False, index=True, comment='平台商品ID/SPUID') # 加索引方便按商品查询

    item_id = Column(String(100), nullable=True, comment='平台订单项ID (如果API提供, v1.0有)')
    resource_id = Column(String(100), nullable=True, comment='资源ID (来自v2.0)')
    resource_type = Column(SmallInteger, nullable=True, comment='资源类型码')

    # 商品信息
    goods_name = Column(String(500), nullable=True, comment='商品名称')
    goods_image = Column(String(500), nullable=True, comment='商品图片URL')
    goods_desc = Column(Text, nullable=True, comment='商品描述')
    goods_sn = Column(String(100), nullable=True, comment='商品编码')
    spu_type = Column(String(50), nullable=True, comment='SPU 类型')

    # SKU信息
    sku_id = Column(String(100), nullable=True, index=True, comment='SKU ID') # 加索引方便按SKU查询
    sku_spec_code = Column(String(100), nullable=True, comment='SKU 规格编码')
    goods_spec_desc = Column(String(500), nullable=True, comment='商品规格描述')

    # 数量与价格 (使用Decimal存储元)
    quantity = Column(Integer, nullable=False, default=1, comment='购买数量') # 合并 buy_num
    unit_price = Column(DECIMAL(10, 2), nullable=True, comment='商品单价 (元)')
    total_price = Column(DECIMAL(10, 2), nullable=True, comment='商品总价 (单价*数量) (元)')
    discount_amount = Column(DECIMAL(10, 2), nullable=True, comment='商品优惠金额 (元)')
    actual_fee = Column(DECIMAL(10, 2), nullable=True, comment='商品实付金额 (元)')
    discount_detail = Column(JSON, nullable=True, comment='优惠详情列表 (JSON存储)')

    # 有效期
    period_type = Column(SmallInteger, nullable=True, comment='有效期类型码')
    expire_desc = Column(String(255), nullable=True, comment='有效期描述')
    expire_start = Column(DateTime, nullable=True, comment='有效期开始时间')
    expire_end = Column(DateTime, nullable=True, comment='有效期结束时间')

    # 状态
    check_state = Column(SmallInteger, nullable=True, comment='核销状态码')
    check_state_desc = Column(String(100), nullable=True, comment='核销状态描述')
    refund_state = Column(SmallInteger, nullable=True, comment='退款状态码')
    refund_state_desc = Column(String(100), nullable=True, comment='退款状态描述')
    ship_state = Column(SmallInteger, nullable=True, comment='发货状态码')
    ship_state_desc = Column(String(100), nullable=True, comment='发货状态描述')

    # 关联信息
    relation_goods_id = Column(String(100), nullable=True, comment='关联商品ID')
    relation_goods_type = Column(SmallInteger, nullable=True, comment='关联商品类型码')
    relation_goods_type_desc = Column(String(100), nullable=True, comment='关联商品类型描述')

    # 系统字段
    first_seen_at = Column(DateTime, default=func.now(), comment='在本系统中首次记录的时间')
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='在本系统的最后更新时间')

    # 关系 (多对一)
    order = relationship("Order", back_populates="order_items",
                         primaryjoin="and_(OrderItem.order_id==Order.order_id, OrderItem.platform==Order.platform)")
    # product = relationship("Product", back_populates="order_items", foreign_keys=[product_id, platform])

    __table_args__ = (
        ForeignKeyConstraint(['platform', 'order_id'], ['orders.platform', 'orders.order_id']),
        ForeignKeyConstraint(['platform', 'product_id'], ['products.platform', 'products.product_id']),
        # 复合唯一约束，确保一个订单下一个商品SKU只有一条记录 (如果sku_id总存在且唯一区分)
        UniqueConstraint('platform', 'order_id', 'product_id', 'sku_id', name='uk_order_item_sku'),
        Index('ix_order_items_order_product_sku', 'platform', 'order_id', 'product_id', 'sku_id'),
        Index('ix_order_items_product', 'platform', 'product_id'), # 按商品查
        Index('ix_order_items_sku', 'platform', 'sku_id'),       # 按SKU查
        {'comment': '订单商品明细表'}
    )

    def __repr__(self):
        return f"<OrderItem(order_id='{self.order_id}', product_id='{self.product_id}', sku_id='{self.sku_id}')>"


class AftersaleOrder(Base):
    __tablename__ = 'aftersale_orders'

    # 使用平台 aftersale_id 和 platform 作为复合主键
    aftersale_id = Column(String(100, collation='utf8mb4_unicode_ci'), primary_key=True, comment='平台售后单ID')
    platform = Column(String(32, collation='utf8mb4_unicode_ci'), primary_key=True, default='xiaoe', comment='来源平台')

    order_id = Column(String(100, collation='utf8mb4_unicode_ci'), nullable=False, index=True, comment='平台父订单ID') # 加索引方便关联查询
    user_id = Column(String(100, collation='utf8mb4_unicode_ci'), nullable=True, index=True, comment='平台用户ID (冗余或通过order关联)') # 加索引方便按用户查询售后

    # 售后状态与类型
    state = Column(SmallInteger, nullable=True, index=True, comment='售后状态码')
    state_str = Column(String(100), nullable=True, comment='售后状态中文名')
    sale_type = Column(SmallInteger, nullable=True, comment='售后方式码')
    sale_type_name = Column(String(50), nullable=True, comment='售后方式中文名')
    ship_state = Column(SmallInteger, nullable=True, comment='退货物流状态码')
    ship_state_str = Column(String(100), nullable=True, comment='退货物流状态中文名')

    # 金额相关 (使用Decimal存储元)
    apply_refund_money = Column(DECIMAL(10, 2), nullable=True, comment='申请退款金额 (元)')
    refund_money = Column(DECIMAL(10, 2), nullable=True, comment='实际退款金额 (元)')

    # 时间相关
    created_at_platform = Column(DateTime, nullable=True, index=True, comment='售后单创建时间 (平台时间)')
    updated_at_platform = Column(DateTime, nullable=True, index=True, comment='售后单更新时间 (平台时间)')
    invalid_time = Column(DateTime, nullable=True, comment='售后单失效时间')
    state_invalid_time = Column(DateTime, nullable=True, comment='状态失效时间')

    # 原因与备注
    reason = Column(Text, nullable=True, comment='买家申请售后原因')
    state_reason = Column(Text, nullable=True, comment='状态原因 (API 可能提供)')
    remark = Column(Text, nullable=True, comment='买家售后备注')
    merchant_remark = Column(Text, nullable=True, comment='商家售后备注')

    # 商品概览 (冗余)
    goods_name_overview = Column(Text, nullable=True, comment='商品名称概览')
    img_url_overview = Column(String(500), nullable=True, comment='商品图片URL概览')
    sku_info_overview = Column(Text, nullable=True, comment='商品规格概览')
    resource_type_str = Column(String(100), nullable=True, comment='资源类型中文名')

    # 其他
    use_collection = Column(SmallInteger, nullable=True, comment='订单渠道 (无需关注)')

    # 系统字段
    first_seen_at = Column(DateTime, default=func.now(), comment='在本系统中首次记录的时间')
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='在本系统的最后更新时间')

    # 关系 (多对一)
    order = relationship("Order", back_populates="aftersale_orders",
                         primaryjoin="and_(AftersaleOrder.order_id==Order.order_id, AftersaleOrder.platform==Order.platform)")
    # user = relationship("User", back_populates="aftersale_orders", foreign_keys=[user_id, platform])
    aftersale_items = relationship("AftersaleItem", back_populates="aftersale_order", cascade="all, delete-orphan",
                                   primaryjoin="and_(AftersaleOrder.aftersale_id==foreign(AftersaleItem.aftersale_id), AftersaleOrder.platform==foreign(AftersaleItem.platform))")

    __table_args__ = (
        ForeignKeyConstraint(['platform', 'order_id'], ['orders.platform', 'orders.order_id']),
        ForeignKeyConstraint(['platform', 'user_id'], ['users.platform', 'users.user_id']), # 如果 user_id 是冗余字段
        Index('ix_aftersale_orders_order_id', 'platform', 'order_id'),
        Index('ix_aftersale_orders_created_at', 'platform', 'created_at_platform'),
        Index('ix_aftersale_orders_updated_at', 'platform', 'updated_at_platform'),
        {'comment': '售后订单主表'}
    )

    def __repr__(self):
        return f"<AftersaleOrder(platform='{self.platform}', aftersale_id='{self.aftersale_id}')>"


class AftersaleItem(Base):
    __tablename__ = 'aftersale_items'

    # 使用自增ID作为主键
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 复合外键关联到 AftersaleOrder 表
    aftersale_id = Column(String(100, collation='utf8mb4_unicode_ci'), nullable=False, comment='平台售后单ID')
    platform = Column(String(32, collation='utf8mb4_unicode_ci'), nullable=False, default='xiaoe', comment='来源平台')

    # 关联哪个原始订单项? 可能需要其他字段匹配
    # order_item_id = Column(BigInteger, nullable=True, comment='关联的原始订单项ID')

    # 商品信息
    goods_name = Column(String(500), nullable=True, comment='商品名称')
    goods_tag = Column(String(100), nullable=True, comment='商品标签')
    img_url = Column(String(500), nullable=True, comment='商品图片URL')
    sku_info = Column(Text, nullable=True, comment='商品规格信息')

    # 数量与价格 (使用Decimal存储元)
    buy_num = Column(Integer, nullable=False, default=1, comment='售后涉及的数量')
    goods_price = Column(DECIMAL(10, 2), nullable=True, comment='商品价格 (元) - 注意: API单位是分')

    # 系统字段
    first_seen_at = Column(DateTime, default=func.now(), comment='在本系统中首次记录的时间')
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='在本系统的最后更新时间')

    # 关系 (多对一)
    aftersale_order = relationship("AftersaleOrder", back_populates="aftersale_items",
                                   primaryjoin="and_(AftersaleItem.aftersale_id==AftersaleOrder.aftersale_id, AftersaleItem.platform==AftersaleOrder.platform)")

    __table_args__ = (
        ForeignKeyConstraint(['platform', 'aftersale_id'], ['aftersale_orders.platform', 'aftersale_orders.aftersale_id']),
        # 复合唯一约束，确保一个售后单下一个商品只有一条记录 (如果能唯一识别商品)
        # UniqueConstraint('platform', 'aftersale_id', 'goods_name', 'sku_info', name='uk_aftersale_item'), # 可能需要调整
        Index('ix_aftersale_items_aftersale_id', 'platform', 'aftersale_id'),
        {'comment': '售后订单商品明细表'}
    )

    def __repr__(self):
        return f"<AftersaleItem(aftersale_id='{self.aftersale_id}', goods_name='{self.goods_name}')>"


# Example usage for engine creation (replace with your actual DB connection string)
# from config.config import settings
# engine = create_engine(settings.DATABASE_URL, echo=True)
# Base.metadata.create_all(engine) 