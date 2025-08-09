"""Add structure aware OCR support

Revision ID: 002_structure_aware_ocr
Revises: 001_initial
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_structure_aware_ocr'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade():
    """Add structure aware OCR field to invoice table"""
    op.add_column('invoices', sa.Column('has_structure_aware_ocr', sa.Boolean(), default=False))

def downgrade():
    """Remove structure aware OCR field from invoice table"""
    op.drop_column('invoices', 'has_structure_aware_ocr')
