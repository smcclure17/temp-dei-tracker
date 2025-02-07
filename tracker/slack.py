from urllib.parse import urlparse

import requests

from tracker.models import ScrapeResult


def format_slack_message(change: ScrapeResult, threshold: float) -> dict:
    """
    Format a Slack message for a page change notification.

    Args:
        change: ScrapeResult object containing change details
        threshold: The similarity threshold that triggered this alert

    Returns:
        dict: Formatted Slack message payload
    """
    # Get domain from URL for quick reference
    domain = urlparse(change.url).netloc

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔄 Page Change Detected: {domain}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Page Title*\n{change.title}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*URL*\n<{change.url}|View Page>"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Similarity Score*\n{round(change.similarity, 3)}"
            }
        }
    ]

    # Only add screenshot section if there's a screenshot URL
    if change.old_screenshot_url:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Screenshot Comparison*\n<{change.old_screenshot_url}|View snapshot of old page capture>"
            }
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Detected at {change.timestamp} with change threshold {threshold}"
            }
        ]
    })

    return {
        "blocks": blocks,
        "text": f"Page change detected on {domain} - {change.similarity} similarity",  # Fallback text
    }


def send_slack_alerts(results: list[ScrapeResult], change_threshold: float) -> None:
    sorted_results = sorted(results)
    for change in sorted_results:
        if change.similarity < change_threshold:
            message = format_slack_message(change, change_threshold)
            try:
                response = requests.post(
                    "https://hooks.slack.com/services/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",
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Failed to send Slack notification for {change.url}: {str(e)}")