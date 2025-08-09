"""Update to complete schema with all template fields

Revision ID: 002_complete_schema
Revises: 001_initial
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_complete_schema'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade():
    # === ATJAUNINĀT INVOICES TABULU ===
    
    # Pievienot papildu piegādātāja banku laukus
    op.add_column('invoices', sa.Column('supplier_bank_name_1', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_account_number_1', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_swift_code_1', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_bank_name_2', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_account_number_2', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_swift_code_2', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_bank_name_3', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_account_number_3', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_swift_code_3', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_bank_name_4', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_account_number_4', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('supplier_swift_code_4', sa.String(), nullable=True))
    
    # Pārdēvēt supplier_reg_number uz supplier_registration_number
    op.alter_column('invoices', 'supplier_reg_number', new_column_name='supplier_registration_number')
    op.alter_column('invoices', 'recipient_reg_number', new_column_name='recipient_registration_number')
    
    # Pievienot trūkstošos laukus
    op.add_column('invoices', sa.Column('carrier_name', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('carrier_vat_number', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('vehicle_number', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('driver_name', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('transaction_type', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('service_period', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('discount', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('total_with_discount', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('amount_with_discount', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('amount_without_discount', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('total_issued', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('weight_kg', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('issued_by', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('total_quantity', sa.Float(), nullable=True))
    op.add_column('invoices', sa.Column('page_number', sa.String(), nullable=True))
    
    # === ATJAUNINĀT SUPPLIERS TABULU ===
    
    # Pārdēvēt reg_number uz registration_number
    op.alter_column('suppliers', 'reg_number', new_column_name='registration_number')
    
    # Pievienot papildu banku laukus
    op.add_column('suppliers', sa.Column('bank_name_1', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('account_number_1', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('swift_code_1', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('bank_name_2', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('account_number_2', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('swift_code_2', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('bank_name_3', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('account_number_3', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('swift_code_3', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('bank_name_4', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('account_number_4', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('swift_code_4', sa.String(), nullable=True))
    
    # Pievienot kontaktinformāciju
    op.add_column('suppliers', sa.Column('contact_person', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('email', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('website', sa.String(), nullable=True))
    op.add_column('suppliers', sa.Column('invoices_count', sa.Integer(), nullable=True, default=0))
    op.add_column('suppliers', sa.Column('last_invoice_date', sa.Date(), nullable=True))
    
    # === ATJAUNINĀT PRODUCTS TABULU ===
    
    # Pievienot papildu laukus priekš produktiem
    op.add_column('products', sa.Column('product_category', sa.String(), nullable=True))
    op.add_column('products', sa.Column('weight', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('dimensions', sa.String(), nullable=True))

def downgrade():
    # Atgriezt izmaiņas (reverse order)
    
    # === PRODUCTS TABULA ===
    op.drop_column('products', 'dimensions')
    op.drop_column('products', 'weight')
    op.drop_column('products', 'product_category')
    
    # === SUPPLIERS TABULA ===
    op.drop_column('suppliers', 'last_invoice_date')
    op.drop_column('suppliers', 'invoices_count')
    op.drop_column('suppliers', 'website')
    op.drop_column('suppliers', 'email')
    op.drop_column('suppliers', 'phone')
    op.drop_column('suppliers', 'contact_person')
    
    op.drop_column('suppliers', 'swift_code_4')
    op.drop_column('suppliers', 'account_number_4')
    op.drop_column('suppliers', 'bank_name_4')
    op.drop_column('suppliers', 'swift_code_3')
    op.drop_column('suppliers', 'account_number_3')
    op.drop_column('suppliers', 'bank_name_3')
    op.drop_column('suppliers', 'swift_code_2')
    op.drop_column('suppliers', 'account_number_2')
    op.drop_column('suppliers', 'bank_name_2')
    op.drop_column('suppliers', 'swift_code_1')
    op.drop_column('suppliers', 'account_number_1')
    op.drop_column('suppliers', 'bank_name_1')
    
    op.alter_column('suppliers', 'registration_number', new_column_name='reg_number')
    
    # === INVOICES TABULA ===
    op.drop_column('invoices', 'page_number')
    op.drop_column('invoices', 'total_quantity')
    op.drop_column('invoices', 'issued_by')
    op.drop_column('invoices', 'weight_kg')
    op.drop_column('invoices', 'total_issued')
    op.drop_column('invoices', 'amount_without_discount')
    op.drop_column('invoices', 'amount_with_discount')
    op.drop_column('invoices', 'total_with_discount')
    op.drop_column('invoices', 'discount')
    op.drop_column('invoices', 'notes')
    op.drop_column('invoices', 'service_period')
    op.drop_column('invoices', 'transaction_type')
    op.drop_column('invoices', 'driver_name')
    op.drop_column('invoices', 'vehicle_number')
    op.drop_column('invoices', 'carrier_vat_number')
    op.drop_column('invoices', 'carrier_name')
    
    op.alter_column('invoices', 'recipient_registration_number', new_column_name='recipient_reg_number')
    op.alter_column('invoices', 'supplier_registration_number', new_column_name='supplier_reg_number')
    
    op.drop_column('invoices', 'supplier_swift_code_4')
    op.drop_column('invoices', 'supplier_account_number_4')
    op.drop_column('invoices', 'supplier_bank_name_4')
    op.drop_column('invoices', 'supplier_swift_code_3')
    op.drop_column('invoices', 'supplier_account_number_3')
    op.drop_column('invoices', 'supplier_bank_name_3')
    op.drop_column('invoices', 'supplier_swift_code_2')
    op.drop_column('invoices', 'supplier_account_number_2')
    op.drop_column('invoices', 'supplier_bank_name_2')
    op.drop_column('invoices', 'supplier_swift_code_1')
    op.drop_column('invoices', 'supplier_account_number_1')
    op.drop_column('invoices', 'supplier_bank_name_1')
