"""add_document_intelligence_schema

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-08-11 16:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'financial_documents',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False, unique=True),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=30), nullable=False, server_default='UNKNOWN'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='UPLOADED'),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('extractor_version', sa.String(length=50), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('user_id', 'checksum', name='uq_fin_docs_user_checksum'),
    )
    op.create_index('ix_fin_docs_user_id', 'financial_documents', ['user_id'], unique=False)
    op.create_index('ix_fin_docs_status', 'financial_documents', ['status'], unique=False)

    op.create_table(
        'document_extractions',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), sa.ForeignKey('financial_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('extraction_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('document_type', sa.String(length=30), nullable=False, server_default='UNKNOWN'),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('extracted_fields', sa.JSON(), nullable=True),
        sa.Column('extracted_transactions', sa.JSON(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('raw_page_count', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.Date(), nullable=True),
        sa.Column('period_end', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_doc_extractions_document_id', 'document_extractions', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_doc_extractions_document_id', table_name='document_extractions')
    op.drop_table('document_extractions')
    op.drop_index('ix_fin_docs_status', table_name='financial_documents')
    op.drop_index('ix_fin_docs_user_id', table_name='financial_documents')
    op.drop_table('financial_documents')
