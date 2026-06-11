from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `urls` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `url` VARCHAR(2048) NOT NULL,
    `alert_before_days` INT NOT NULL DEFAULT 30,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `alerts` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `alert_type` VARCHAR(20) NOT NULL,
    `message` LONGTEXT NOT NULL,
    `is_sent` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `url_id` INT NOT NULL,
    CONSTRAINT `fk_alerts_urls_f9961a65` FOREIGN KEY (`url_id`) REFERENCES `urls` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `daily_health_summaries` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `date` DATE NOT NULL,
    `checks_count` INT NOT NULL,
    `avg_ttfb_ms` DOUBLE,
    `min_ttfb_ms` DOUBLE,
    `max_ttfb_ms` DOUBLE,
    `min_ssl_days_remaining` INT,
    `healthy_count` INT NOT NULL,
    `unhealthy_count` INT NOT NULL,
    `last_http_status` INT,
    `last_ssl_expiration_date` DATETIME(6),
    `last_checked_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `url_id` INT NOT NULL,
    UNIQUE KEY `uid_daily_healt_url_id_133c3a` (`url_id`, `date`),
    CONSTRAINT `fk_daily_he_urls_5ce78414` FOREIGN KEY (`url_id`) REFERENCES `urls` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `health_checks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `http_status` INT,
    `ttfb_ms` DOUBLE,
    `ssl_expiration_date` DATETIME(6),
    `ssl_days_remaining` INT,
    `is_healthy` BOOL NOT NULL DEFAULT 0,
    `error_message` LONGTEXT,
    `checked_at` DATETIME(6) NOT NULL,
    `url_id` INT NOT NULL,
    CONSTRAINT `fk_health_c_urls_7322cc73` FOREIGN KEY (`url_id`) REFERENCES `urls` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
