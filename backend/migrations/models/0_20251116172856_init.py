from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "organizations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "organizations"."name" IS 'Organization name (must be unique)';
COMMENT ON TABLE "organizations" IS 'Organization model for multi-tenant architecture.';
CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "role" VARCHAR(10) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
CREATE INDEX IF NOT EXISTS "idx_users_organiz_d1d822" ON "users" ("organization_id");
COMMENT ON COLUMN "users"."role" IS 'User role (master/slave)';
COMMENT ON TABLE "users" IS 'User model for authentication and authorization.';
CREATE TABLE IF NOT EXISTS "projects" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_projects_organiz_4dcd73" ON "projects" ("organization_id");
COMMENT ON TABLE "projects" IS 'Project model for organizing tasks and time entries.';
CREATE TABLE IF NOT EXISTS "tasks" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "project_id" UUID NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_tasks_project_78d187" ON "tasks" ("project_id");
COMMENT ON TABLE "tasks" IS 'Task model for granular work tracking within projects.';
CREATE TABLE IF NOT EXISTS "time_entries" (
    "id" UUID NOT NULL PRIMARY KEY,
    "start_time" TIMESTAMPTZ NOT NULL,
    "end_time" TIMESTAMPTZ,
    "is_running" BOOL NOT NULL DEFAULT False,
    "is_billable" BOOL NOT NULL DEFAULT True,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE,
    "project_id" UUID NOT NULL REFERENCES "projects" ("id") ON DELETE CASCADE,
    "task_id" UUID REFERENCES "tasks" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_time_entrie_is_runn_057b73" ON "time_entries" ("is_running");
CREATE INDEX IF NOT EXISTS "idx_time_entrie_organiz_785e00" ON "time_entries" ("organization_id");
CREATE INDEX IF NOT EXISTS "idx_time_entrie_project_2c3fd1" ON "time_entries" ("project_id");
CREATE INDEX IF NOT EXISTS "idx_time_entrie_task_id_dc2571" ON "time_entries" ("task_id");
CREATE INDEX IF NOT EXISTS "idx_time_entrie_user_id_391944" ON "time_entries" ("user_id");
COMMENT ON TABLE "time_entries" IS 'Time entry model for tracking time spent on tasks.';
CREATE TABLE IF NOT EXISTS "tags" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "organization_id" UUID NOT NULL REFERENCES "organizations" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_tags_name_980564" UNIQUE ("name", "organization_id")
);
CREATE INDEX IF NOT EXISTS "idx_tags_organiz_fc5836" ON "tags" ("organization_id");
COMMENT ON TABLE "tags" IS 'Tag model for categorizing and labeling time entries.';
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
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "time_entry_tags" (
    "time_entries_id" UUID NOT NULL REFERENCES "time_entries" ("id") ON DELETE CASCADE,
    "tag_id" UUID NOT NULL REFERENCES "tags" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_time_entry__time_en_29f6a9" ON "time_entry_tags" ("time_entries_id", "tag_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
