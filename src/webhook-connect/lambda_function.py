import os

def lambda_handler(event, context):
    token = os.environ['META_WPP_WEBHOOK_TOKEN']

    print("EVENTO RECEBIDO:", event)

    params = event.get("queryStringParameters", {})

    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == token:
        challenge = int(params.get("hub.challenge"))
        return challenge
    else:
        return {
            "statusCode": 403,
            "body": "Token inválido"
        }