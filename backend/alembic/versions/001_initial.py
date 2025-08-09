"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-07-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create suppliers table
    op.create_table('suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('name_variations', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('registration_number', sa.String(length=100), nullable=True),
        sa.Column('vat_number', sa.String(length=50), nullable=True),
        sa.Column('recognition_patterns', sa.Text(), nullable=True),
        sa.Column('confidence_threshold', sa.Float(), nullable=True, default=0.8),
        sa.Column('times_processed', sa.Integer(), nullable=True, default=0),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('accuracy_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_suppliers_id'), 'suppliers', ['id'], unique=False)
    op.create_index('idx_suppliers_name', 'suppliers', ['name'], unique=False)
    op.create_index('idx_suppliers_active', 'suppliers', ['is_active'], unique=False)

    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=True),
        sa.Column('supplier_confidence', sa.Float(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column('delivery_date', sa.DateTime(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True, default='EUR'),
        sa.Column('status', sa.String(length=50), nullable=True, default='uploaded'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_manually_corrected', sa.Boolean(), nullable=True, default=False),
        sa.Column('correction_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)
    op.create_index('idx_invoices_supplier', 'invoices', ['supplier_name'], unique=False)
    op.create_index('idx_invoices_date', 'invoices', ['invoice_date'], unique=False)
    op.create_index('idx_invoices_status', 'invoices', ['status'], unique=False)
    op.create_index('idx_invoices_created_at', 'invoices', ['created_at'], unique=False)

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('product_code', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('vat_rate', sa.Float(), nullable=True),
        sa.Column('vat_amount', sa.Float(), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('is_manually_corrected', sa.Boolean(), nullable=True, default=False),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index('idx_products_invoice_id', 'products', ['invoice_id'], unique=False)
    op.create_index('idx_products_name', 'products', ['name'], unique=False)

    # Create error_corrections table
    op.create_table('error_corrections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('original_value', sa.Text(), nullable=False),
        sa.Column('corrected_value', sa.Text(), nullable=False),
        sa.Column('surrounding_text', sa.Text(), nullable=True),
        sa.Column('confidence_before', sa.Float(), nullable=True),
        sa.Column('confidence_after', sa.Float(), nullable=True),
        sa.Column('matched_pattern', sa.Text(), nullable=True),
        sa.Column('suggested_pattern', sa.Text(), nullable=True),
        sa.Column('correction_source', sa.String(length=50), nullable=True, default='manual'),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('is_applied_to_model', sa.Boolean(), nullable=True, default=False),
        sa.Column('application_date', sa.DateTime(), nullable=True),
        sa.Column('effectiveness_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_error_corrections_id'), 'error_corrections', ['id'], unique=False)
    op.create_index('idx_errors_type', 'error_corrections', ['error_type'], unique=False)
    op.create_index('idx_errors_invoice', 'error_corrections', ['invoice_id'], unique=False)
    op.create_index('idx_errors_created', 'error_corrections', ['created_at'], unique=False)

    # Insert some sample suppliers
    op.execute("""
        INSERT INTO suppliers (name, name_variations, is_verified) VALUES 
        ('SIA PIEMĒRS', '["SIA PIEMĒRS", "PIEMĒRS SIA", "Piemērs"]', true),
        ('AS TESTS', '["AS TESTS", "TESTS AS", "A/S TESTS"]', true)
    """)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('error_corrections')
    op.drop_table('products')
    op.drop_table('invoices')
    op.drop_table('suppliers')
