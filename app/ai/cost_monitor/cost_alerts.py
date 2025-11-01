# app/ai/cost_monitor/cost_alerts.py
import os
import requests
from datetime import datetime
from typing import Dict, Any

try:
    from app.ai.cost_monitor.usage_tracker import UsageTracker
except Exception:
    # graceful fallback if tracker missing
    UsageTracker = None

SLACK_WEBHOOK = os.getenv("COST_ALERT_SLACK_WEBHOOK", "").strip()
DAILY_THRESHOLD = float(os.getenv("COST_ALERT_DAILY_THRESHOLD_USD", "2.0"))

def check_and_alert(day: str = None) -> Dict[str, Any]:
    """
    Check today's cost against threshold. If exceeded and webhook set, send Slack alert.
    Returns a dict describing totals and whether an alert was sent.
    """
    day = day or datetime.utcnow().strftime("%Y-%m-%d")
    result: Dict[str, Any] = {"date": day, "daily_total": 0.0, "threshold": DAILY_THRESHOLD, "alert_sent": False}

    if UsageTracker is None:
        result["error"] = "UsageTracker not available"
        return result

    try:
        tracker = UsageTracker()
        daily = tracker.get_daily(day)
        total_cost = float(daily.get("cost", 0.0))
        result["daily_total"] = round(total_cost, 8)

        if total_cost > DAILY_THRESHOLD:
            result["exceeded"] = True
            if SLACK_WEBHOOK:
                payload = {"text": f"ALERT: LLM cost for {day} = ${total_cost:.4f} (threshold ${DAILY_THRESHOLD})"}
                try:
                    r = requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
                    result["alert_sent"] = True
                    result["slack_status"] = r.status_code
                except Exception as e:
                    result["alert_error"] = str(e)
            else:
                # Slack not configured — still indicate we would have alerted
                result["alert_sent"] = False
                result["note"] = "SLACK_WEBHOOK not configured"
        else:
            result["exceeded"] = False

    except Exception as e:
        result["error"] = str(e)

    return result
