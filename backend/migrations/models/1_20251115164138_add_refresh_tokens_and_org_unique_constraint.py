from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "refresh_tokens" (
    "id" UUID NOT NULL PRIMARY KEY,
    "token_hash" VARCHAR(64) NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "revoked_at" TIMESTAMPTZ,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_refresh_tok_token_h_e92003" ON "refresh_tokens" ("token_hash");
CREATE INDEX IF NOT EXISTS "idx_refresh_tok_user_id_915374" ON "refresh_tokens" ("user_id", "token_hash");
COMMENT ON COLUMN "refresh_tokens"."token_hash" IS 'SHA-256 hash of the refresh token';
COMMENT ON COLUMN "refresh_tokens"."expires_at" IS 'When this refresh token expires';
COMMENT ON COLUMN "refresh_tokens"."revoked_at" IS 'Timestamp when token was revoked (logout/security event)';
COMMENT ON COLUMN "refresh_tokens"."user_id" IS 'User who owns this refresh token';
COMMENT ON TABLE "refresh_tokens" IS 'Refresh token storage for revocation capability.';
        COMMENT ON COLUMN "organizations"."name" IS 'Organization name (must be unique)';
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_organizatio_name_75f36f" ON "organizations" ("name");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "organizations" DROP CONSTRAINT IF EXISTS "organizations_name_key";
        DROP INDEX IF EXISTS "uid_organizatio_name_75f36f";
        COMMENT ON COLUMN "organizations"."name" IS NULL;
        DROP TABLE IF EXISTS "refresh_tokens";"""


MODELS_STATE = (
    "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"
)
