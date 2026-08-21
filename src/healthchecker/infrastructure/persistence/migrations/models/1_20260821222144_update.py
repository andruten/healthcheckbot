from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `urls` MODIFY COLUMN `updated_at` DATETIME(6) NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `urls` MODIFY COLUMN `updated_at` DATETIME(6) NOT NULL DEFAULT NULL;"""


MODELS_STATE = (
    "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"
)
