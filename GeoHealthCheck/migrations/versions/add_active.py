"""empty message

Revision ID: f17ae1f9a0be
Revises: 992013af402f
Create Date: 2017-09-08 12:24:18.038337

"""
from alembic import op
import sqlalchemy as sa
import imp
import os


# revision identifiers, used by Alembic.
revision = 'f17ae1f9a0be'
down_revision = '992013af402f'
branch_labels = None
depends_on = None

alembic_helpers = imp.load_source('alembic_helpers', (
    os.getcwd() + '/' + op.get_context().script.dir + '/alembic_helpers.py'))

def upgrade():
    if not alembic_helpers.table_has_column('resource', 'active'):
        from sqlalchemy.sql import table, column
        print('Column active not present in resource table, will create')
        op.add_column(u'resource', sa.Column('active', sa.Boolean, nullable=True, default=True))
        resource = table('resource', column('active'))
        op.execute(resource.update().values(active=True))
        op.alter_column('resource', 'active', nullable=False)
    else:
        print('Column active already present in resource table')


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    print('Dropping Column active from resource table')
    op.drop_column(u'resource', 'active')
