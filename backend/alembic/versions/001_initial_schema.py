"""Initial schema — pgvector, all tables, all indexes

Revision ID: 001
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── users ───────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.Text, nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False,
                  server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false')),
        sa.Column('plan',
                  sa.Enum('FREE', 'PRO', 'TEAM', name='plantype'),
                  nullable=False, server_default='FREE'),
        sa.Column('stripe_customer_id', sa.String(255), unique=True),
        sa.Column('stripe_subscription_id', sa.String(255), unique=True),
        sa.Column('subscription_ends_at', sa.DateTime(timezone=True)),
        sa.Column('monthly_analysis_count', sa.Integer, nullable=False,
                  server_default=sa.text('0')),
        sa.Column('total_analysis_count', sa.Integer, nullable=False,
                  server_default=sa.text('0')),
        sa.Column('monthly_reset_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # ── analyses ────────────────────────────────────────────────────────────
    op.create_table(
        'analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jurisdiction', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(500)),
        sa.Column('lease_type',
                  sa.Enum('RESIDENTIAL', 'COMMERCIAL', 'UNKNOWN', name='leasetype'),
                  server_default='UNKNOWN'),
        sa.Column('pages_analyzed', sa.Integer, server_default=sa.text('0')),
        sa.Column('fairness_score', sa.Integer),
        sa.Column('lease_summary', postgresql.JSONB),
        sa.Column('risk_summary', postgresql.JSONB),
        sa.Column('clauses', postgresql.JSONB),
        sa.Column('top_3_priorities', postgresql.JSONB),
        sa.Column('counter_proposal_letter', sa.Text),
        sa.Column('processing_time_ms', sa.Integer),
        sa.Column('tokens_used', sa.Integer),
        sa.Column('model_used', sa.String(100)),
        sa.Column('is_deleted', sa.Integer, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('purge_after', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_analyses_user_id', 'analyses', ['user_id'])
    op.create_index('idx_analyses_created_at', 'analyses', ['created_at'])
    # BUG-45 FIX: index for purge script (SELECT WHERE purge_after < NOW())
    op.create_index('idx_analyses_purge_after', 'analyses', ['purge_after'])
    # BUG-45 FIX: composite index for history queries (user_id + jurisdiction)
    op.create_index('idx_analyses_user_jurisdiction', 'analyses',
                    ['user_id', 'jurisdiction'])

    # ── legal_chunks (RAG vector store) ─────────────────────────────────────
    op.create_table(
        'legal_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('source', sa.String(500), nullable=False),
        sa.Column('section_ref', sa.String(200)),
        sa.Column('jurisdiction_tag', sa.String(100)),
        sa.Column('chunk_index', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )
    # pgvector column — raw SQL because sqlalchemy doesn't know the type yet
    op.execute(
        'ALTER TABLE legal_chunks '
        'ADD COLUMN IF NOT EXISTS embedding vector(1024)'
    )
    op.execute(
        'CREATE INDEX IF NOT EXISTS idx_legal_chunks_embedding '
        'ON legal_chunks USING ivfflat (embedding vector_cosine_ops) '
        'WITH (lists = 100)'
    )
    op.create_index('idx_legal_chunks_jurisdiction', 'legal_chunks',
                    ['jurisdiction_tag'])

    # ── audit_log ────────────────────────────────────────────────────────────
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', sa.String(200)),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.Text),
        sa.Column('extra_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )
    op.create_index('idx_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('idx_audit_log_created_at', 'audit_log', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('legal_chunks')
    op.drop_table('analyses')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS plantype')
    op.execute('DROP TYPE IF EXISTS leasetype')
