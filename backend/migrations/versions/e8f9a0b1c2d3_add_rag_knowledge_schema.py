"""add_rag_knowledge_schema

Revision ID: e8f9a0b1c2d3
Revises: c3f8be1f809b
Create Date: 2026-08-11 15:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'c3f8be1f809b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable vector extension on PostgreSQL dialect
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        vector_type = Vector(384)
    else:
        vector_type = sa.JSON()

    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('authority', sa.String(length=30), nullable=False, server_default='GENERAL'),
        sa.Column('category', sa.String(length=30), nullable=False, server_default='GENERAL_FINANCE'),
        sa.Column('country', sa.String(length=3), nullable=False, server_default='IND'),
        sa.Column('jurisdiction', sa.String(length=50), nullable=False, server_default='India'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('review_date', sa.Date(), nullable=True),
        sa.Column('document_hash', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_knowledge_documents_hash', 'knowledge_documents', ['document_hash'], unique=False)
    op.create_index('ix_knowledge_documents_status_category', 'knowledge_documents', ['status', 'category'], unique=False)

    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('embedding', vector_type, nullable=True),
        sa.Column('chunk_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_knowledge_chunks_doc_index', 'knowledge_chunks', ['document_id', 'chunk_index'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_knowledge_chunks_doc_index', table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')
    op.drop_index('ix_knowledge_documents_status_category', table_name='knowledge_documents')
    op.drop_index('ix_knowledge_documents_hash', table_name='knowledge_documents')
    op.drop_table('knowledge_documents')
