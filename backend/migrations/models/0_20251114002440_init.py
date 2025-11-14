from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "organizations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
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
    "task_id" UUID NOT NULL REFERENCES "tasks" ("id") ON DELETE CASCADE,
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
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_time_entry__time_en_29f6a9" ON "time_entry_tags" ("time_entries_id", "tag_id");
-- Custom constraint: Only one running timer per user (partial unique index)
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_time_entries_running_user" ON "time_entries" ("user_id") WHERE "is_running" = true;
-- Custom constraint: end_time must be >= start_time
ALTER TABLE "time_entries" ADD CONSTRAINT "chk_end_time_after_start" CHECK ("end_time" IS NULL OR "end_time" >= "start_time");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "time_entry_tags";
        DROP TABLE IF EXISTS "time_entries";
        DROP TABLE IF EXISTS "tags";
        DROP TABLE IF EXISTS "tasks";
        DROP TABLE IF EXISTS "projects";
        DROP TABLE IF EXISTS "users";
        DROP TABLE IF EXISTS "organizations";
        """


MODELS_STATE = (
    "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"
)
