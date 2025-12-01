from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text, JSON, 
    ForeignKey, Index, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class ComplaintStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class BillerStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(100), unique=True, index=True, nullable=False)
    client_name = Column(String(255), nullable=False)
    client_secret_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    scopes = Column(JSON, default=list)
    rate_limit = Column(Integer, default=100)
    
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    webhook_url = Column(String(500))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    api_keys = relationship("APIKey", back_populates="client")
    transactions = relationship("Transaction", back_populates="client")
    
    __table_args__ = (
        Index("idx_clients_active", "is_active"),
    )


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(100))
    scopes = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="api_keys")


class Biller(Base):
    __tablename__ = "billers"
    
    id = Column(Integer, primary_key=True, index=True)
    biller_id = Column(String(50), unique=True, index=True, nullable=False)
    biller_name = Column(String(255), nullable=False)
    biller_alias = Column(String(255))
    category = Column(String(100), index=True)
    sub_category = Column(String(100))
    
    status = Column(SQLEnum(BillerStatus), default=BillerStatus.ACTIVE, index=True)
    is_adhoc = Column(Boolean, default=False)
    supports_billvalidation = Column(Boolean, default=True)
    supports_payment = Column(Boolean, default=True)
    
    biller_logo = Column(String(500))
    biller_description = Column(Text)
    coverage = Column(String(100))
    
    min_amount = Column(Float, default=0)
    max_amount = Column(Float, default=1000000)
    
    payment_modes = Column(JSON, default=list)
    payment_channels = Column(JSON, default=list)
    
    response_time = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    mdm_records = relationship("BillerMDM", back_populates="biller")
    input_params = relationship("BillerInputParam", back_populates="biller")
    transactions = relationship("Transaction", back_populates="biller")
    
    __table_args__ = (
        Index("idx_billers_category_status", "category", "status"),
        Index("idx_billers_name_search", "biller_name"),
    )


class BillerMDM(Base):
    __tablename__ = "biller_mdm"
    
    id = Column(Integer, primary_key=True, index=True)
    biller_id = Column(String(50), ForeignKey("billers.biller_id"), index=True)
    
    mdm_type = Column(String(50), index=True)
    mdm_key = Column(String(100))
    mdm_value = Column(Text)
    mdm_data = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True))
    effective_to = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    biller = relationship("Biller", back_populates="mdm_records")
    
    __table_args__ = (
        Index("idx_mdm_biller_type", "biller_id", "mdm_type"),
        UniqueConstraint("biller_id", "mdm_type", "mdm_key", name="uq_biller_mdm"),
    )


class BillerInputParam(Base):
    __tablename__ = "biller_input_params"
    
    id = Column(Integer, primary_key=True, index=True)
    biller_id = Column(String(50), ForeignKey("billers.biller_id"), index=True)
    
    param_name = Column(String(100), nullable=False)
    param_label = Column(String(255))
    param_type = Column(String(50), default="text")
    is_mandatory = Column(Boolean, default=True)
    min_length = Column(Integer)
    max_length = Column(Integer)
    regex_pattern = Column(String(500))
    options = Column(JSON)
    order_index = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    biller = relationship("Biller", back_populates="input_params")
    
    __table_args__ = (
        Index("idx_input_params_biller", "biller_id"),
    )


class Bank(Base):
    __tablename__ = "banks"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(String(20), unique=True, index=True, nullable=False)
    bank_name = Column(String(255), nullable=False)
    bank_code = Column(String(20))
    bank_type = Column(String(50))
    
    logo_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    supports_imps = Column(Boolean, default=True)
    supports_neft = Column(Boolean, default=True)
    supports_rtgs = Column(Boolean, default=True)
    supports_upi = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    ifsc_codes = relationship("BankIFSC", back_populates="bank")
    
    __table_args__ = (
        Index("idx_banks_name", "bank_name"),
        Index("idx_banks_active", "is_active"),
    )


class BankIFSC(Base):
    __tablename__ = "bank_ifsc"
    
    id = Column(Integer, primary_key=True, index=True)
    ifsc_code = Column(String(20), unique=True, index=True, nullable=False)
    bank_id = Column(String(20), ForeignKey("banks.bank_id"), index=True)
    
    branch_name = Column(String(255))
    branch_code = Column(String(20))
    address = Column(Text)
    city = Column(String(100), index=True)
    district = Column(String(100))
    state = Column(String(100), index=True)
    contact = Column(String(50))
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    bank = relationship("Bank", back_populates="ifsc_codes")
    
    __table_args__ = (
        Index("idx_ifsc_bank_city", "bank_id", "city"),
        Index("idx_ifsc_state", "state"),
    )


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    reference_id = Column(String(50), index=True)
    
    client_id = Column(Integer, ForeignKey("clients.id"), index=True)
    biller_id = Column(String(50), ForeignKey("billers.biller_id"), index=True)
    
    consumer_number = Column(String(100))
    consumer_name = Column(String(255))
    consumer_mobile = Column(String(20))
    consumer_email = Column(String(255))
    
    bill_amount = Column(Float, nullable=False)
    convenience_fee = Column(Float, default=0)
    total_amount = Column(Float, nullable=False)
    
    payment_mode = Column(String(50))
    payment_channel = Column(String(50))
    
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, index=True)
    status_message = Column(Text)
    
    bbps_transaction_id = Column(String(100), index=True)
    bbps_reference_id = Column(String(100))
    bbps_response = Column(JSON)
    
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    client = relationship("Client", back_populates="transactions")
    biller = relationship("Biller", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_txn_client_status", "client_id", "status"),
        Index("idx_txn_biller_date", "biller_id", "created_at"),
        Index("idx_txn_date", "created_at"),
    )


class BillFetchRecord(Base):
    __tablename__ = "bill_fetch_records"
    
    id = Column(Integer, primary_key=True, index=True)
    fetch_id = Column(String(50), unique=True, index=True, nullable=False)
    
    biller_id = Column(String(50), index=True)
    consumer_number = Column(String(100))
    
    input_params = Column(JSON)
    
    bill_amount = Column(Float)
    bill_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    bill_period = Column(String(50))
    bill_number = Column(String(100))
    
    customer_name = Column(String(255))
    
    response_code = Column(String(20))
    response_message = Column(Text)
    raw_response = Column(JSON)
    
    is_successful = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_fetch_biller_consumer", "biller_id", "consumer_number"),
        Index("idx_fetch_date", "created_at"),
    )


class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, index=True, nullable=False)
    
    transaction_id = Column(String(50), index=True)
    biller_id = Column(String(50), index=True)
    
    complainant_name = Column(String(255))
    complainant_mobile = Column(String(20))
    complainant_email = Column(String(255))
    
    complaint_type = Column(String(100), index=True)
    complaint_description = Column(Text)
    
    status = Column(SQLEnum(ComplaintStatus), default=ComplaintStatus.OPEN, index=True)
    resolution = Column(Text)
    
    assigned_to = Column(String(100))
    priority = Column(String(20), default="medium")
    
    bbps_complaint_id = Column(String(100))
    bbps_response = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index("idx_complaint_status", "status"),
        Index("idx_complaint_type", "complaint_type"),
        Index("idx_complaint_date", "created_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    entity_type = Column(String(50), index=True)
    entity_id = Column(String(100), index=True)
    
    action = Column(String(50), nullable=False)
    actor_id = Column(String(100))
    actor_type = Column(String(50))
    
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_date", "created_at"),
    )


class CSVUpload(Base):
    __tablename__ = "csv_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String(50), unique=True, index=True, nullable=False)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    upload_type = Column(String(50), index=True)
    
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    success_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    status = Column(String(50), default="pending", index=True)
    error_message = Column(Text)
    processing_log = Column(JSON)
    
    uploaded_by = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index("idx_csv_type_status", "upload_type", "status"),
        Index("idx_csv_date", "created_at"),
    )
