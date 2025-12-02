"""Initial schema for Company Researcher

Revision ID: 0001
Revises: None
Create Date: 2024-12-01

DATA-002: PostgreSQL schema design implementation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('ticker', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'country', name='uq_company_name_country')
    )
    op.create_index('ix_companies_name_lower', 'companies', ['name'], unique=False)

    # Research runs table
    op.create_table(
        'research_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='taskstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('total_sources', sa.Integer(), default=0),
        sa.Column('total_insights', sa.Integer(), default=0),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_runs_task_id', 'research_runs', ['task_id'], unique=True)
    op.create_index('ix_research_runs_status', 'research_runs', ['status'], unique=False)
    op.create_index('ix_research_runs_created_at', 'research_runs', ['created_at'], unique=False)

    # Sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('research_run_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('source_type', sa.Enum('WEB', 'PDF', 'SEC_FILING', 'NEWS', 'SOCIAL', 'VIDEO', 'API', 'OTHER', name='sourcetype'), nullable=False),
        sa.Column('content_snippet', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.Column('published_date', sa.DateTime(), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['research_run_id'], ['research_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sources_domain', 'sources', ['domain'], unique=False)
    op.create_index('ix_sources_url_hash', 'sources', ['content_hash'], unique=False)
    op.create_index('ix_sources_source_type', 'sources', ['source_type'], unique=False)

    # Insights table
    op.create_table(
        'insights',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('research_run_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Enum('FINANCIAL', 'MARKET', 'COMPETITOR', 'BRAND', 'SALES', 'INVESTMENT', 'SOCIAL_MEDIA', 'GENERAL', name='insightcategory'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('is_key_finding', sa.Boolean(), default=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['research_run_id'], ['research_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_insights_category', 'insights', ['category'], unique=False)
    op.create_index('ix_insights_is_key_finding', 'insights', ['is_key_finding'], unique=False)

    # Citations table
    op.create_table(
        'citations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('insight_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('quote', sa.Text(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['insight_id'], ['insights.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('insight_id', 'source_id', name='uq_citation_insight_source')
    )

    # Search cache table
    op.create_table(
        'search_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('query_hash', sa.String(64), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('results', sa.JSON(), nullable=False),
        sa.Column('result_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_cache_query_hash', 'search_cache', ['query_hash'], unique=True)

    # Usage metrics table
    op.create_table(
        'usage_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), default=0),
        sa.Column('output_tokens', sa.Integer(), default=0),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('cost_usd', sa.Float(), default=0.0),
        sa.Column('requests_total', sa.Integer(), default=0),
        sa.Column('requests_failed', sa.Integer(), default=0),
        sa.Column('requests_cached', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'provider', name='uq_usage_date_provider')
    )
    op.create_index('ix_usage_metrics_date', 'usage_metrics', ['date'], unique=False)
    op.create_index('ix_usage_metrics_provider', 'usage_metrics', ['provider'], unique=False)


def downgrade() -> None:
    op.drop_table('usage_metrics')
    op.drop_table('search_cache')
    op.drop_table('citations')
    op.drop_table('insights')
    op.drop_table('sources')
    op.drop_table('research_runs')
    op.drop_table('companies')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS sourcetype")
    op.execute("DROP TYPE IF EXISTS insightcategory")
