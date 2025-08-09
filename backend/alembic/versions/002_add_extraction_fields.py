"""Pievienot jaunus laukus invoice tabulai

Revision ID: 002_add_extraction_fields
Revises: 001_initial
Create Date: 2025-01-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_extraction_fields'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Pievienot jaunus laukus
    op.add_column('invoices', sa.Column('extracted_text', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('ocr_confidence', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('ocr_strategy', sa.String(50), nullable=True))
    op.add_column('invoices', sa.Column('invoice_number', sa.String(100), nullable=True))
    op.add_column('invoices', sa.Column('vat_amount', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('reg_number', sa.String(50), nullable=True))
    op.add_column('invoices', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('bank_account', sa.String(50), nullable=True))
    op.add_column('invoices', sa.Column('uploaded_at', sa.DateTime(), nullable=True))
    op.add_column('invoices', sa.Column('started_at', sa.DateTime(), nullable=True))
    
    # Atjaunināt uploaded_at ar created_at vērtību eksistējošiem ierakstiem
    op.execute("UPDATE invoices SET uploaded_at = created_at WHERE uploaded_at IS NULL")


def downgrade():
    # Noņemt pievienotos laukus
    op.drop_column('invoices', 'started_at')
    op.drop_column('invoices', 'uploaded_at')
    op.drop_column('invoices', 'bank_account')
    op.drop_column('invoices', 'address')
    op.drop_column('invoices', 'reg_number')
    op.drop_column('invoices', 'vat_amount')
    op.drop_column('invoices', 'invoice_number')
    op.drop_column('invoices', 'ocr_strategy')
    op.drop_column('invoices', 'ocr_confidence')
    op.drop_column('invoices', 'extracted_text')
