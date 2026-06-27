"""Schema consolidation — model_variants deduplication and missing defaults.

Revision ID: c00000000005
Revises: c00000000004
Create Date: 2026-06-22

Addressing:
- B2#6: Add quantization_id FK on model_variants → quantizations
- B2#13: Establish FK relationship to quantizations table (schema debt cleanup)
- Add server_default=sa.func.now() on model_variants.created_at/updated_at
- Add server_default=sa.func.now() on model_catalog.created_at

The model_variants table has overlapping columns with quantizations:
  - bits_per_param / quantization_bits   → quantizations.bits_per_param
  - quality_multiplier / speed_multiplier → quantizations.quality_score / speed_multiplier

These duplicate columns still exist on model_variants for application compatibility.
This migration adds the FK reference so future work can cleanly migrate to quantizations.
"""

import sqlalchemy as sa
from alembic import op

revision = "c00000000005"
down_revision = "c00000000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Add quantization_id FK on model_variants → quantizations ────
    op.add_column(
        "model_variants",
        sa.Column("quantization_id", sa.Integer(), nullable=True),
    )

    # Backfill quantization_id by matching model_variants.quantization
    # to quantizations.name.  Variants without a matching quantization
    # entry will remain NULL — those are legacy rows or custom quants.
    op.execute(
        "UPDATE model_variants "
        "SET quantization_id = quantizations.id "
        "FROM quantizations "
        "WHERE LOWER(TRIM(quantizations.name)) = LOWER(TRIM(model_variants.quantization))"
    )

    op.create_index(
        "ix_model_variants_quantization_id",
        "model_variants",
        ["quantization_id"],
    )
    op.create_foreign_key(
        "fk_model_variants_quantization_id",
        "model_variants",
        "quantizations",
        ["quantization_id"],
        ["id"],
    )

    # ── 2. Fix missing server_default on model_variants timestamps ─────
    # These columns were created without server_default in the baseline.
    # We alter to add server_default for new rows only.
    op.execute(
        "ALTER TABLE model_variants "
        "ALTER COLUMN created_at SET DEFAULT now()"
    )
    op.execute(
        "ALTER TABLE model_variants "
        "ALTER COLUMN updated_at SET DEFAULT now()"
    )

    # ── 3. Fix model_catalog.created_at missing server_default ─────────
    op.execute(
        "ALTER TABLE model_catalog "
        "ALTER COLUMN created_at SET DEFAULT now()"
    )

    # ── 4. Document schema debt for future cleanup ─────────────────────
    # SCHEMA DEBT NOTE:
    # model_variants still has duplicate columns that overlap with quantizations:
    #   - bits_per_param / quantization_bits  (→ quantizations.bits_per_param)
    #   - quality_multiplier                   (→ quantizations.quality_score)
    #   - speed_multiplier                     (→ quantizations.speed_multiplier)
    #
    # These are kept for backwards compatibility with application code that
    # reads them directly.  A future migration should:
    #   1. Audit all code paths reading these columns
    #   2. Switch to join via quantization_id → quantizations
    #   3. Drop the duplicate columns with:
    #      op.drop_column("model_variants", "bits_per_param")
    #      op.drop_column("model_variants", "quantization_bits")
    #      op.drop_column("model_variants", "quality_multiplier")
    #      op.drop_column("model_variants", "speed_multiplier")


def downgrade() -> None:
    # ── Reverse FK and index ───────────────────────────────────────────
    op.drop_constraint("fk_model_variants_quantization_id", "model_variants", type_="foreignkey")
    op.drop_index("ix_model_variants_quantization_id", table_name="model_variants")
    op.drop_column("model_variants", "quantization_id")

    # ── Reverse server_default changes ─────────────────────────────────
    op.execute(
        "ALTER TABLE model_catalog "
        "ALTER COLUMN created_at DROP DEFAULT"
    )
    op.execute(
        "ALTER TABLE model_variants "
        "ALTER COLUMN updated_at DROP DEFAULT"
    )
    op.execute(
        "ALTER TABLE model_variants "
        "ALTER COLUMN created_at DROP DEFAULT"
    )
