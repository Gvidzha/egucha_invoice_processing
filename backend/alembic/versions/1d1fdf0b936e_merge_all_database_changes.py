"""Merge all database changes

Revision ID: 1d1fdf0b936e
Revises: 002_add_structure_analysis, 002_structure_aware_ocr, 5cbbe3ab536c
Create Date: 2025-08-03 08:57:51.759293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d1fdf0b936e'
down_revision = ('002_add_structure_analysis', '002_structure_aware_ocr', '5cbbe3ab536c')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
