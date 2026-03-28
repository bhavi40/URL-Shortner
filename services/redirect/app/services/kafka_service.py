from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
import json
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger

class KafkaService:
    """
    Kafka producer for publishing click events.
    Fire and forget — never block the redirect for Kafka.
    """

    def __init__(self):
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        """Start Kafka producer on app startup."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",              # wait for all replicas to acknowledge
                retries=3,              # retry 3 times on failure
                retry_backoff_ms=100,   # wait 100ms between retries
                request_timeout_ms=5000 # 5 second timeout
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            # App still works without Kafka — log and continue
            logger.error(f"Kafka producer failed to start: {e}")
            self.producer = None

    async def stop(self):
        """Stop Kafka producer on app shutdown."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def publish_click_event(
        self,
        short_code: str,
        user_id: str,
        ip_address: str,
        user_agent: str,
        referrer: str | None
    ) -> None:
        """
        Publish click event to Kafka.
        Never raises — redirect must not fail because of Kafka.
        """
        if not self.producer:
            logger.warning("Kafka producer not available — click event dropped")
            return

        event = {
            "short_code": short_code,
            "user_id": user_id,
            "clicked_at": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "referrer": referrer,
            "event_type": "click"
        }

        try:
            await self.producer.send_and_wait(
                settings.KAFKA_TOPIC_CLICKS,
                value=event,
                key=short_code.encode("utf-8")  # same short_code → same partition
            )
            logger.debug(f"Click event published for {short_code}")
        except Exception as e:
            # NEVER let Kafka failure break redirects
            logger.error(f"Failed to publish click event for {short_code}: {e}")

# Global instance
kafka_service = KafkaService()