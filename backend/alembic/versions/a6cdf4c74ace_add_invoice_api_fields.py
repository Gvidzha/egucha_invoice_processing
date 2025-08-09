"""add_invoice_api_fields

Revision ID: a6cdf4c74ace
Revises: 002_add_extraction_fields
Create Date: 2025-07-31 15:17:53.142480

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6cdf4c74ace'
down_revision = '002_add_extraction_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pievienojam tikai tos laukus, kas neeksistē
    op.add_column('invoices', sa.Column('processing_status', sa.String(50), default='pending'))
    op.add_column('invoices', sa.Column('processing_started_at', sa.DateTime))
    op.add_column('invoices', sa.Column('processing_completed_at', sa.DateTime))
    op.add_column('invoices', sa.Column('bank_account', sa.String(50)))
    op.add_column('invoices', sa.Column('reg_number', sa.String(50)))


def downgrade() -> None:
    # Noņemam pievienotos laukus
    op.drop_column('invoices', 'reg_number')
    op.drop_column('invoices', 'bank_account')
    op.drop_column('invoices', 'processing_completed_at')
    op.drop_column('invoices', 'processing_started_at')
    op.drop_column('invoices', 'processing_status')
