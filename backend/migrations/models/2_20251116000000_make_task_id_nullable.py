from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Make task_id nullable to allow tracking time on projects without specific tasks
        ALTER TABLE "time_entries" ALTER COLUMN "task_id" DROP NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Reverse: Make task_id NOT NULL again
        -- WARNING: This will fail if there are any NULL task_id values
        ALTER TABLE "time_entries" ALTER COLUMN "task_id" SET NOT NULL;"""
