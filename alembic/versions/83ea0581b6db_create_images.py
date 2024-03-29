"""Create images

Revision ID: 83ea0581b6db
Revises: 154b6b3f2c16
Create Date: 2023-11-20 19:28:11.987477

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83ea0581b6db'
down_revision = "99d9e8ba1d28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('images',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.Column('location', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('location')
    )
    op.add_column('users', sa.Column('avatar_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(None, 'users', 'images', ['avatar_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'avatar_id')
    op.drop_table('images')
    # ### end Alembic commands ###
