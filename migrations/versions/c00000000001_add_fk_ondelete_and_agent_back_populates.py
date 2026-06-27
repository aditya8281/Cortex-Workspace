"""Add ON DELETE clauses to FKs and Agent↔User back_populates.

Revision ID: c00000000001
Revises: b00000000000
Create Date: 2026-06-22 00:00:00.000000
"""

from alembic import op

revision = "c00000000001"
down_revision = "b00000000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ModelVariant FKs → SET NULL
    op.execute(
        "ALTER TABLE model_variants "
        "DROP CONSTRAINT IF EXISTS model_variants_provider_id_fkey, "
        "ADD CONSTRAINT model_variants_provider_id_fkey "
        "FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE model_variants "
        "DROP CONSTRAINT IF EXISTS model_variants_provider_model_id_fkey, "
        "ADD CONSTRAINT model_variants_provider_model_id_fkey "
        "FOREIGN KEY (provider_model_id) REFERENCES provider_models(id) ON DELETE SET NULL"
    )

    # ModelDownload FKs → SET NULL
    op.execute(
        "ALTER TABLE model_downloads "
        "DROP CONSTRAINT IF EXISTS model_downloads_model_variant_id_fkey, "
        "ADD CONSTRAINT model_downloads_model_variant_id_fkey "
        "FOREIGN KEY (model_variant_id) REFERENCES model_variants(id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE model_downloads "
        "DROP CONSTRAINT IF EXISTS model_downloads_user_id_fkey, "
        "ADD CONSTRAINT model_downloads_user_id_fkey "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"
    )

    # ModelUsage FKs → SET NULL
    op.execute(
        "ALTER TABLE model_usage "
        "DROP CONSTRAINT IF EXISTS model_usage_model_variant_id_fkey, "
        "ADD CONSTRAINT model_usage_model_variant_id_fkey "
        "FOREIGN KEY (model_variant_id) REFERENCES model_variants(id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE model_usage "
        "DROP CONSTRAINT IF EXISTS model_usage_user_id_fkey, "
        "ADD CONSTRAINT model_usage_user_id_fkey "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"
    )


def downgrade() -> None:
    # Revert ModelUsage FKs (drop ondelete)
    op.execute(
        "ALTER TABLE model_usage "
        "DROP CONSTRAINT IF EXISTS model_usage_user_id_fkey, "
        "ADD CONSTRAINT model_usage_user_id_fkey "
        "FOREIGN KEY (user_id) REFERENCES users(id)"
    )
    op.execute(
        "ALTER TABLE model_usage "
        "DROP CONSTRAINT IF EXISTS model_usage_model_variant_id_fkey, "
        "ADD CONSTRAINT model_usage_model_variant_id_fkey "
        "FOREIGN KEY (model_variant_id) REFERENCES model_variants(id)"
    )

    # Revert ModelDownload FKs
    op.execute(
        "ALTER TABLE model_downloads "
        "DROP CONSTRAINT IF EXISTS model_downloads_user_id_fkey, "
        "ADD CONSTRAINT model_downloads_user_id_fkey "
        "FOREIGN KEY (user_id) REFERENCES users(id)"
    )
    op.execute(
        "ALTER TABLE model_downloads "
        "DROP CONSTRAINT IF EXISTS model_downloads_model_variant_id_fkey, "
        "ADD CONSTRAINT model_downloads_model_variant_id_fkey "
        "FOREIGN KEY (model_variant_id) REFERENCES model_variants(id)"
    )

    # Revert ModelVariant FKs
    op.execute(
        "ALTER TABLE model_variants "
        "DROP CONSTRAINT IF EXISTS model_variants_provider_model_id_fkey, "
        "ADD CONSTRAINT model_variants_provider_model_id_fkey "
        "FOREIGN KEY (provider_model_id) REFERENCES provider_models(id)"
    )
    op.execute(
        "ALTER TABLE model_variants "
        "DROP CONSTRAINT IF EXISTS model_variants_provider_id_fkey, "
        "ADD CONSTRAINT model_variants_provider_id_fkey "
        "FOREIGN KEY (provider_id) REFERENCES providers(id)"
    )
