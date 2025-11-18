from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        COMMENT ON COLUMN "users"."role" IS 'User role (boss/worker)';
        ALTER TABLE "projects" ADD "color" VARCHAR(7) NOT NULL DEFAULT '#3b82f6';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        COMMENT ON COLUMN "users"."role" IS 'User role (master/slave)';
        ALTER TABLE "projects" DROP COLUMN "color";"""


MODELS_STATE = (
    "eJztXWtTGzkW/Ssq74eFqkAmhECK2pkqQ8iGnRCmwGymJqRccrdsa92WeiQ1jneW/773qh"
    "/ul982tpP+EkDqe1s6ep0j3Vb+qvWlyzx9eKM6VPD/UsOlqJ2Rv2qC9hn8Upr/gtSo749y"
    "McHQlmcNZOpJm0Nb2ijqGMhsU08zSHKZdhT3o5fV0s6JdUnaUpF+4Bl+YJigwhCqnC43zD"
    "GBYofo1pUO+OWis5CHB/EgLqnTJeniEsV8xTQTRhNKNPOpooYRR/Z9KoYvIZ2bIQk0vJSY"
    "LiN6qA3rg6+65xEJKYrYZzjTZC/QTOkXxFfyP/BO+M1Q3YMfzDiH+6TFPIleJKEiUwZbt0"
    "DwPwPWNLLD0CvU8MtXSObCZd+Yjv/0e802Z56baS/uogOb3jRD36bd31+9e2+fRNxaTUd6"
    "QV+MnvaHpitF8ngQcPcQbTCvwwRDFNxU84nA86LmjpPCEkOCUQFLiuqOElzWptAa6P8f7U"
    "A4Fm/7Jvzn+JdaoVvgW3LtHCU50LOgS3FoJ6z7U1irUZ1tag1fdfGhfrv3+mTf1lJq01E2"
    "0yJSe7KG1NDQ1OI6AtL+LEB50aWqHMr4+RyYUND1wBjDM2EoYZHIXj/QBvobCX3v58dOOa"
    "a1Pv3W9JjomC78efTmzQSQ/12/tTjDU9a7hNEezgWfoqyjMA8BHwHsKIaANKkpwvwOcgzv"
    "s3Kos5Y5wN3I9DD+ZRH444QR/qOpa2IDzNxpa1AH90Z4w6htJ+DbuLq+vGvUr3/DmvS1/t"
    "OzENUbl5hzZFOHudS9k1xTJE7I56vGB4J/kj9uPl3mR0byXOOPGpaJBkY2hRw0qZvqhnFq"
    "DMwTzkftXmogYUKLOr0BVW4zkzPqAXaKLDb+eWT2/tdb5iUrTq6Zo3XpHlxsZwM/xb02Th"
    "019AiBeHVYDoTfQi87jAOO0yasnQqWzuWwaICnS3A03GU0aGdZFGhnx+qP84U8kuNmkGJW"
    "/6ifT6GCdmyp8d34pvQkUUJq48ljPJlNZqjpJBadpagnzJBdJINOuBRT4dokqdI8L8Nh53"
    "WAFPYu8H2pgK6agSRKekyfPYgD0pJan5G62+eCDLjpkjYAQi5u798R6jhMaySeGeaLNAgt"
    "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"
    "m2FUhUDkfMxxbqVGB+dlS/VzLixP/wf/Sgsr"
)
