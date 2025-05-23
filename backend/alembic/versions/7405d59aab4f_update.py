"""update

Revision ID: 7405d59aab4f
Revises: 053afded2b51
Create Date: 2025-02-02 02:30:31.722127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7405d59aab4f'
down_revision: Union[str, None] = '053afded2b51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 구조체 ENUM 생성 (StructEnum)
    struct_enum = sa.Enum('ST', '경량ST', 'SRC', 'RC', '석조', '벽돌조', name='structenum')
    struct_enum.create(op.get_bind(), checkfirst=True)

    # 위치 ENUM 생성 (PlaceEnum)
    place_enum = sa.Enum('구내', '구외', name='placeenum')
    place_enum.create(op.get_bind(), checkfirst=True)

    # 안전 등급 ENUM 생성 (SafetyEnum)
    safety_enum = sa.Enum('A', 'B', 'C', name='safetyenum')
    safety_enum.create(op.get_bind(), checkfirst=True)
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'subjects', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True), sa.Column('name', sa.String(), nullable=False),
        sa.Column('level', sa.Enum('대학', '대학원', name='levelenum'), nullable=True),
        sa.Column(
            'type',
            sa.Enum('교양 필수', '교양 선택', '전공 필수', '전공 선택', '전공 기초', '교직 과목', name='subjecttypeenum'),
            nullable=False
        ), sa.Column('grade', sa.Enum('1', '2', '3', '4', name='gradeenum'), nullable=True),
        sa.Column('code', sa.String(), nullable=False), sa.ForeignKeyConstraint(
            ['department_id'],
            ['departments.id'],
        ), sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'association', sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('building_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ['building_id'],
            ['buildings.id'],
        ), sa.ForeignKeyConstraint(
            ['department_id'],
            ['departments.id'],
        ), sa.PrimaryKeyConstraint('department_id', 'building_id', 'id')
    )
    op.create_table(
        'courses', sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('professor_id', sa.Integer(), nullable=True), sa.Column('semester_id', sa.Integer(), nullable=True),
        sa.Column('group', sa.Integer(), nullable=False), sa.Column('is_online', sa.String(), nullable=True),
        sa.Column('is_english', sa.Boolean(), nullable=True), sa.Column('credit', sa.Float(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ['professor_id'],
            ['professors.id'],
        ), sa.ForeignKeyConstraint(
            ['semester_id'],
            ['semesters.id'],
        ), sa.ForeignKeyConstraint(
            ['subject_id'],
            ['subjects.id'],
        ), sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'timetables', sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('day_of_week', sa.String(), nullable=False), sa.Column('building_id', sa.Integer(), nullable=True),
        sa.Column('classroom', sa.String(), nullable=False), sa.Column('st_time', sa.Time(), nullable=True),
        sa.Column('ed_time', sa.Time(), nullable=True), sa.Column('is_remote', sa.Boolean(), nullable=True),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ['building_id'],
            ['buildings.id'],
        ), sa.ForeignKeyConstraint(
            ['course_id'],
            ['courses.id'],
        ), sa.PrimaryKeyConstraint('id')
    )
    op.add_column('buildings', sa.Column('place', sa.Enum('구내', '구외', name='placeenum'), nullable=False))
    op.add_column(
        'buildings',
        sa.Column('structure', sa.Enum('ST', '경량ST', 'SRC', 'RC', '석조', '벽돌조', name='structenum'), nullable=False)
    )
    op.add_column('buildings', sa.Column('floor_under', sa.Integer(), nullable=False))
    op.add_column('buildings', sa.Column('floor_above', sa.Integer(), nullable=False))
    op.add_column('buildings', sa.Column('completion', sa.String(), nullable=False))
    op.add_column('buildings', sa.Column('building_area', sa.Integer(), nullable=False))
    op.add_column('buildings', sa.Column('total_floor_area', sa.Integer(), nullable=False))
    op.add_column('buildings', sa.Column('year_elapsed', sa.Integer(), nullable=False))
    op.add_column('buildings', sa.Column('safety', sa.Enum('A', 'B', 'C', name='safetyenum'), nullable=False))
    op.add_column('buildings', sa.Column('main_department', sa.String(), nullable=False))
    op.alter_column('calendars', 'st_date', existing_type=sa.DATE(), type_=sa.DateTime(), existing_nullable=False)
    op.alter_column('calendars', 'ed_date', existing_type=sa.DATE(), type_=sa.DateTime(), existing_nullable=False)
    op.alter_column('calendars', 'semester_id', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('notice_attachments', 'attachment_id', new_column_name='id')
    op.alter_column('notice_content_chunks', 'chunk_id', new_column_name='id')
    op.alter_column('professor_detail_chunks', 'chunk_id', new_column_name='id')
    op.alter_column('support_attachments', 'attachment_id', new_column_name='id')
    op.alter_column('support_content_chunks', 'chunk_id', new_column_name='id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('support_content_chunks', sa.Column('chunk_id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_column('support_content_chunks', 'id')
    op.add_column('support_attachments', sa.Column('attachment_id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_column('support_attachments', 'id')
    op.add_column('professor_detail_chunks', sa.Column('chunk_id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_column('professor_detail_chunks', 'id')
    op.add_column('notice_content_chunks', sa.Column('chunk_id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_column('notice_content_chunks', 'id')
    op.add_column('notice_attachments', sa.Column('attachment_id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_column('notice_attachments', 'id')
    op.alter_column('calendars', 'semester_id', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('calendars', 'ed_date', existing_type=sa.DateTime(), type_=sa.DATE(), existing_nullable=False)
    op.alter_column('calendars', 'st_date', existing_type=sa.DateTime(), type_=sa.DATE(), existing_nullable=False)
    op.drop_column('buildings', 'main_department')
    op.drop_column('buildings', 'safety')
    op.drop_column('buildings', 'year_elapsed')
    op.drop_column('buildings', 'total_floor_area')
    op.drop_column('buildings', 'building_area')
    op.drop_column('buildings', 'completion')
    op.drop_column('buildings', 'floor_above')
    op.drop_column('buildings', 'floor_under')
    op.drop_column('buildings', 'structure')
    op.drop_column('buildings', 'place')
    op.drop_table('timetables')
    op.drop_table('courses')
    op.drop_table('association')
    op.drop_table('subjects')
    # ### end Alembic commands ###
