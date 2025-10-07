from dirtviz_slack_bot.cli import entry

def lambda_handler(event, context):
    entry()
    return {"status": "ok"}

