from sqlalchemy import ( 
    create_engine, Column, Integer, String, DateTime, Float, Boolean, 
    ForeignKey, Text, JSON, Numeric
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import datetime

# Create a base class for declarative models
Base = declarative_base()

# --- Dimension Tables ---
class XiaoeUser(Base):
    """小鹅通用户表模型"""
    __tablename__ = 'dim_xiaoe_user'

    user_id = Column(String(100), primary_key=True, comment='小鹅通用户唯一ID')
    user_nickname = Column(String(255), nullable=True, comment='用户昵称')
    bind_phone = Column(String(50), nullable=True, comment='绑定手机号')
    avatar_url = Column(Text, nullable=True, comment='头像URL')
    source = Column(String(50), nullable=True, comment='用户来源描述 (如: 微信)')
    total_paid_amount = Column(Numeric(12, 2), nullable=True, comment='累计消费金额 (元)')
    purchase_count = Column(Integer, nullable=True, comment='购买次数')
    wx_union_id = Column(String(100), nullable=True, comment='微信 Union ID')
    wx_open_id = Column(String(100), nullable=True, comment='微信 Open ID (公众号)')
    wx_app_open_id = Column(String(100), nullable=True, comment='微信 Open ID (小程序)')
    created_at = Column(DateTime, nullable=True, comment='用户创建时间')
    
    # Timestamps for ETL
    etl_inserted_at = Column(DateTime, server_default=func.now(), comment='ETL插入时间')
    etl_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='ETL更新时间')

    # Relationships (optional, useful if querying within app)
    # orders = relationship("XiaoeOrder", back_populates="user")

class XiaoeGoods(Base):
    """小鹅通商品表模型"""
    __tablename__ = 'dim_xiaoe_goods'

    goods_resource_id = Column(String(100), primary_key=True, comment='商品资源ID (主键)')
    spu_id = Column(String(100), index=True, nullable=True, comment='商品SPU ID')
    goods_internal_id = Column(Integer, nullable=True, comment='小鹅通内部商品ID')
    goods_name = Column(String(500), nullable=True, comment='商品名称')
    resource_type = Column(Integer, nullable=True, comment='资源类型代码')
    spu_type = Column(String(50), nullable=True, comment='SPU类型代码 (如: VDO, ENT)')
    goods_category_id = Column(String(100), nullable=True, comment='商品分类ID')
    goods_tag = Column(String(255), nullable=True, comment='商品标签')
    sell_type = Column(Integer, nullable=True, comment='售卖方式 (1-独立, 2-关联)')
    sale_status = Column(Integer, nullable=True, comment='上架状态 (0-下架, 1-上架, 2-待上架)')
    price_low = Column(Numeric(12, 2), nullable=True, comment='最低价 (元)')
    price_high = Column(Numeric(12, 2), nullable=True, comment='最高价 (元)')
    price_line = Column(Numeric(12, 2), nullable=True, comment='划线价 (元)')
    created_at = Column(DateTime, nullable=True, comment='商品创建时间')
    updated_at = Column(DateTime, nullable=True, comment='商品更新时间')
    sale_at = Column(DateTime, nullable=True, comment='上架时间')
    is_deleted = Column(Boolean, default=False, comment='是否删除')
    is_display = Column(Boolean, default=True, comment='是否显示')
    is_stop_sell = Column(Boolean, default=False, comment='是否停售')
    is_forbid = Column(Boolean, default=False, comment='是否封禁')
    visit_count = Column(Integer, nullable=True, comment='访问次数')
    appraise_count = Column(Integer, nullable=True, comment='评价数')
    sell_count = Column(Integer, nullable=True, comment='销量 (来自extend字段)')
    stock_deduct_mode = Column(Integer, nullable=True, comment='扣库存方式 (0-付款减, 1-拍下减)')
    limit_purchase = Column(Integer, nullable=True, comment='限购数量')
    has_distribute = Column(Boolean, default=False, comment='是否参与分销')
    freight = Column(Numeric(10, 2), nullable=True, comment='运费 (元)')
    freight_template_id = Column(String(100), nullable=True, comment='运费模板ID')
    img_url = Column(Text, nullable=True, comment='商品压缩图URL')
    main_img_urls = Column(JSON, nullable=True, comment='商品主图URL列表 (JSON)')

    # Timestamps for ETL
    etl_inserted_at = Column(DateTime, server_default=func.now(), comment='ETL插入时间')
    etl_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='ETL更新时间')

# --- Fact Tables ---

class XiaoeOrder(Base):
    """小鹅通订单表模型 (事实表)"""
    __tablename__ = 'fact_xiaoe_order'

    order_id = Column(String(100), primary_key=True, comment='订单ID (主键)')
    user_id = Column(String(100), ForeignKey('dim_xiaoe_user.user_id'), index=True, nullable=True, comment='用户ID (外键)')
    created_at = Column(DateTime, nullable=True, comment='下单时间')
    paid_at = Column(DateTime, nullable=True, comment='支付时间')
    updated_at = Column(DateTime, nullable=True, comment='订单更新时间')
    settled_at = Column(DateTime, nullable=True, comment='结算时间')
    order_state = Column(Integer, nullable=True, comment='订单状态代码')
    pay_state = Column(Integer, nullable=True, comment='支付状态代码')
    settle_state = Column(Integer, nullable=True, comment='结算状态代码')
    aftersale_show_state = Column(Integer, nullable=True, comment='售后显示状态代码')
    order_type = Column(Integer, nullable=True, comment='订单类型代码')
    pay_type = Column(Integer, nullable=True, comment='支付类型代码')
    trade_id = Column(String(100), nullable=True, comment='支付交易号')
    app_id = Column(String(100), nullable=True, comment='店铺App ID')
    
    goods_original_total_price = Column(Numeric(12, 2), nullable=True, comment='商品原总价 (元)')
    total_price = Column(Numeric(12, 2), nullable=True, comment='订单总金额 (含运费优惠等) (元)')
    actual_fee = Column(Numeric(12, 2), nullable=True, comment='实际支付金额 (元)')
    discount_amount = Column(Numeric(12, 2), nullable=True, comment='订单级优惠金额 (元)')
    freight_price = Column(Numeric(10, 2), nullable=True, comment='运费 (元)')
    total_modified_amount = Column(Numeric(12, 2), nullable=True, comment='总改价金额 (元)')

    ship_receiver = Column(String(255), nullable=True, comment='收货人姓名')
    ship_phone = Column(String(50), nullable=True, comment='收货人手机')
    ship_province = Column(String(100), nullable=True, comment='收货省份')
    ship_city = Column(String(100), nullable=True, comment='收货城市')
    ship_county = Column(String(100), nullable=True, comment='收货区县')
    ship_detail = Column(Text, nullable=True, comment='详细收货地址')
    ship_company = Column(String(100), nullable=True, comment='快递公司')
    ship_express_id = Column(String(100), nullable=True, comment='快递单号')
    shipped_at = Column(DateTime, nullable=True, comment='发货时间')
    ship_confirmed_at = Column(DateTime, comment='确认收货时间')
    
    # Foreign Key to Users table for promoter - Allow NULLs
    promoter_user_id = Column(String(100), ForeignKey('dim_xiaoe_user.user_id'), nullable=True, comment='推广员用户ID')
    promoter_nickname = Column(String(255), nullable=True, comment='推广员昵称')
    buyer_comment = Column(Text, nullable=True, comment='买家留言')
    
    # Timestamps for ETL
    etl_inserted_at = Column(DateTime, server_default=func.now(), comment='ETL插入时间')
    etl_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='ETL更新时间')

    # Relationships (optional but useful for ORM queries)
    user = relationship("XiaoeUser", foreign_keys=[user_id])
    promoter = relationship("XiaoeUser", foreign_keys=[promoter_user_id])
    items = relationship("XiaoeOrderItem", back_populates="order")

class XiaoeOrderItem(Base):
    """小鹅通订单商品项模型 (事实表)"""
    __tablename__ = 'fact_xiaoe_order_item'

    order_item_id = Column(Integer, primary_key=True, autoincrement=True, comment='代理主键')
    order_id = Column(String(100), ForeignKey('fact_xiaoe_order.order_id'), index=True, nullable=False, comment='订单ID (外键)')
    goods_resource_id = Column(String(100), ForeignKey('dim_xiaoe_goods.goods_resource_id'), index=True, nullable=True, comment='商品资源ID (外键)')
    goods_spu_id = Column(String(100), index=True, nullable=True, comment='商品SPU ID')
    sku_id = Column(String(100), index=True, nullable=True, comment='商品SKU ID')
    goods_name = Column(String(500), nullable=True, comment='商品名称 (冗余)')
    sku_spec_description = Column(String(255), nullable=True, comment='SKU规格描述 (冗余)')
    quantity = Column(Integer, nullable=True, comment='购买数量')
    unit_price = Column(Numeric(12, 2), nullable=True, comment='商品单价 (元)')
    total_price = Column(Numeric(12, 2), nullable=True, comment='商品行总价 (元)')
    resource_type = Column(Integer, nullable=True, comment='资源类型代码 (冗余)')
    refund_state = Column(Integer, nullable=True, comment='退款状态代码')
    ship_state = Column(Integer, nullable=True, comment='发货状态代码')

    # Timestamps for ETL
    etl_inserted_at = Column(DateTime, server_default=func.now(), comment='ETL插入时间')
    etl_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='ETL更新时间')
    
    order = relationship("XiaoeOrder", back_populates="items")
    # goods = relationship("XiaoeGoods")

class XiaoeAftersale(Base):
    """小鹅通售后单模型 (事实表)"""
    __tablename__ = 'fact_xiaoe_aftersale'

    aftersale_id = Column(String(100), primary_key=True, comment='售后单ID (主键)')
    order_id = Column(String(100), ForeignKey('fact_xiaoe_order.order_id'), index=True, nullable=False, comment='关联订单ID (外键)')
    state = Column(Integer, nullable=True, comment='售后状态代码')
    state_description = Column(String(100), nullable=True, comment='售后状态描述')
    sale_type = Column(Integer, nullable=True, comment='售后类型代码 (1-退款, 2-退货退款)')
    sale_type_name = Column(String(50), nullable=True, comment='售后类型名称')
    apply_refund_amount = Column(Numeric(12, 2), nullable=True, comment='申请退款金额 (元)')
    actual_refund_amount = Column(Numeric(12, 2), nullable=True, comment='实际退款金额 (元)')
    reason = Column(Text, nullable=True, comment='售后原因')
    buyer_remark = Column(Text, nullable=True, comment='买家备注')
    merchant_remark = Column(Text, nullable=True, comment='商家备注')
    state_reason = Column(Text, nullable=True, comment='状态原因')
    created_at = Column(DateTime, nullable=True, comment='售后单创建时间')
    updated_at = Column(DateTime, nullable=True, comment='售后单更新时间')
    invalid_at = Column(DateTime, nullable=True, comment='售后单失效时间')
    state_invalid_at = Column(DateTime, nullable=True, comment='当前状态失效时间')
    main_goods_name = Column(String(500), nullable=True, comment='涉及的主要商品名称 (冗余)')
    main_sku_id = Column(String(100), nullable=True, comment='涉及的主要商品SKU ID (冗余)')
    main_sku_info = Column(String(255), nullable=True, comment='涉及的主要商品SKU描述 (冗余)')
    order_actual_fee = Column(Numeric(12, 2), nullable=True, comment='原订单支付金额 (元, 冗余)')

    # Timestamps for ETL
    etl_inserted_at = Column(DateTime, server_default=func.now(), comment='ETL插入时间')
    etl_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='ETL更新时间')

    # Relationships (optional)
    # order = relationship("XiaoeOrder", back_populates="aftersales")
    items = relationship("XiaoeAftersaleItem", back_populates="aftersale")

class XiaoeAftersaleItem(Base):
    """小鹅通售后单商品项模型 (事实表)"""
    __tablename__ = 'fact_xiaoe_aftersale_item'
    
    aftersale_item_id = Column(Integer, primary_key=True, autoincrement=True, comment='代理主键')
    aftersale_id = Column(String(100), ForeignKey('fact_xiaoe_aftersale.aftersale_id'), index=True, nullable=False, comment='售后单ID (外键)')
    # Note: No direct goods_resource_id link from API data, relying on names/sku
    goods_name = Column(String(500), nullable=True, comment='商品名称 (冗余)')
    sku_info = Column(String(255), nullable=True, comment='SKU规格信息 (冗余)')
    quantity = Column(Integer, nullable=True, comment='售后数量')
    price = Column(Numeric(12, 2), nullable=True, comment='商品价格 (元, 冗余)')
    goods_tag = Column(String(100), nullable=True, comment='商品标签 (冗余)')
    img_url = Column(Text, nullable=True, comment='商品图片URL (冗余)')
    
    # Timestamps for ETL
    etl_inserted_at = Column(DateTime, server_default=func.now(), comment='ETL插入时间')
    etl_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='ETL更新时间')

    aftersale = relationship("XiaoeAftersale", back_populates="items")

# --- ETL Control/State Table ---

class SyncState(Base):
    """记录各同步任务的状态，用于增量同步"""
    __tablename__ = 'sync_state'

    sync_type = Column(String(50), primary_key=True, comment='同步类型 (e.g., users, goods, orders, aftersales)')
    # Use JSON to store flexible state like cursor objects
    last_processed_cursor = Column(JSON, nullable=True, comment='最后处理的游标 (用于用户同步等)') 
    last_processed_page = Column(Integer, nullable=True, comment='最后处理的页码 (用于商品同步等)')
    last_processed_timestamp = Column(DateTime, nullable=True, comment='最后处理的时间戳 (用于订单/售后同步)')
    last_run_status = Column(String(20), nullable=True, comment='上次运行状态 (e.g., success, failed)')
    last_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='状态更新时间')

    def __repr__(self):
        return (
            f"<SyncState(sync_type='{self.sync_type}', "
            f"cursor={self.last_processed_cursor}, page={self.last_processed_page}, "
            f"timestamp={self.last_processed_timestamp}, status='{self.last_run_status}')>"
        )

