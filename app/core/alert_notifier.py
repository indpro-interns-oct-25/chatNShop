"""
alert_notifier.py
Handles escalation alerts from the DecisionEngine.
Sends alerts to Slack, Microsoft Teams, or a generic webhook endpoint.
Falls back to structured logging if no webhook is configured.
"""
import os
import json
import logging
import requests

logger = logging.getLogger("alert_notifier")
logger.setLevel(logging.INFO)


def send_alert(event_type: str, context: dict):
    """
    Sends an escalation alert to the configured webhook or logs it locally.

    Args:
        event_type (str): The type of alert (e.g., 'LLM_FALLBACK_TRIGGERED')
        context (dict): Additional context such as query text, alert_id, etc.
    """
    webhook_url = os.getenv("ESCALATION_WEBHOOK_URL")
    payload = {
        "event_type": event_type,
        "context": context,
        "severity": "warning",
    }

    # ✅ 1. Try to send to webhook if configured
    if webhook_url:
        try:
            response = requests.post(webhook_url, json=payload, timeout=3)
            if response.status_code == 200:
                logger.info(f"Escalation sent successfully to webhook: {event_type}")
            else:
                logger.warning(
                    f"Webhook escalation failed with {response.status_code}: {response.text}"
                )
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}", exc_info=True)
    else:
        # ✅ 2. Fallback to structured log only
        logger.warning(f"[ESCALATION] {json.dumps(payload, indent=2)}")
