from cli import entry

def lambda_handler(event, context):
    entry()
    return {"status": "ok"}

