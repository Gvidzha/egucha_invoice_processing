"""Add document structure analysis fields to Invoice model

Revision ID: 002_add_structure_analysis
Revises: 001_initial
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_structure_analysis'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add structure analysis fields to invoices table for POSM 4.5"""
    # Add document structure analysis columns
    op.add_column('invoices', sa.Column('document_structure', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('detected_zones', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('table_regions', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('structure_confidence', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('has_structure_analysis', sa.Boolean(), nullable=True, default=False))
    op.add_column('invoices', sa.Column('structure_analyzed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove structure analysis fields from invoices table"""
    op.drop_column('invoices', 'structure_analyzed_at')
    op.drop_column('invoices', 'has_structure_analysis')
    op.drop_column('invoices', 'structure_confidence')
    op.drop_column('invoices', 'table_regions')
    op.drop_column('invoices', 'detected_zones')
    op.drop_column('invoices', 'document_structure')
