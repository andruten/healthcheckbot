from tortoise import fields, models


class UrlModel(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    url = fields.CharField(max_length=2048)
    alert_before_days = fields.IntField(default=30)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "urls"


class HealthCheckModel(models.Model):
    id = fields.IntField(pk=True)
    url = fields.ForeignKeyField("models.UrlModel", related_name="health_checks")
    http_status = fields.IntField(null=True)
    ttfb_ms = fields.FloatField(null=True)
    ssl_expiration_date = fields.DatetimeField(null=True)
    ssl_days_remaining = fields.IntField(null=True)
    is_healthy = fields.BooleanField(default=False)
    error_message = fields.TextField(null=True)
    checked_at = fields.DatetimeField()

    class Meta:
        table = "health_checks"

    class PydanticMeta:
        exclude = ("url",)


class AlertModel(models.Model):
    id = fields.IntField(pk=True)
    url = fields.ForeignKeyField("models.UrlModel", related_name="alerts")
    alert_type = fields.CharField(max_length=20)
    message = fields.TextField()
    is_sent = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "alerts"

    class PydanticMeta:
        exclude = ("url",)


class DailySummaryModel(models.Model):
    id = fields.IntField(pk=True)
    url = fields.ForeignKeyField("models.UrlModel", related_name="daily_summaries")
    date = fields.DateField()
    checks_count = fields.IntField()
    avg_ttfb_ms = fields.FloatField(null=True)
    min_ttfb_ms = fields.FloatField(null=True)
    max_ttfb_ms = fields.FloatField(null=True)
    min_ssl_days_remaining = fields.IntField(null=True)
    healthy_count = fields.IntField()
    unhealthy_count = fields.IntField()
    last_http_status = fields.IntField(null=True)
    last_ssl_expiration_date = fields.DatetimeField(null=True)
    last_checked_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "daily_health_summaries"
        unique_together = (("url", "date"),)

    class PydanticMeta:
        exclude = ("url",)
