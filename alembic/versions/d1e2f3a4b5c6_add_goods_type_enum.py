"""add_goods_type_enum

Revision ID: d1e2f3a4b5c6
Revises: c022c92e13f8
Create Date: 2026-05-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c022c92e13f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

goods_type_enum = sa.Enum(
    'BUILDING_MATERIALS', 'EVENT_MANAGEMENT', 'CERAMIC_SANITARY',
    'PAINTS_CHEMICALS', 'ELECTRICAL', 'ELECTRONICS', 'FMCG',
    'HOMEMADE_FOOD', 'FURNITURE', 'GENERAL_GOODS', 'HARDWARES',
    'HOUSE_SHIFTING', 'MACHINES_EQUIPMENT', 'PHARMACEUTICAL',
    'PLASTIC_PRODUCTS', 'RUBBER_PRODUCTS', 'TEXTILES_GARMENTS',
    'TIMBERS_PLYWOODS', 'STATIONERY_GIFTS', 'OTHER',
    name='goodstype'
)


def upgrade() -> None:
    goods_type_enum.create(op.get_bind(), checkfirst=True)

    op.execute("""
        ALTER TABLE deliveries 
        ALTER COLUMN goods_type TYPE goodstype 
        USING goods_type::goodstype
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE deliveries 
        ALTER COLUMN goods_type TYPE VARCHAR 
        USING goods_type::VARCHAR
    """)

    goods_type_enum.drop(op.get_bind(), checkfirst=True)
