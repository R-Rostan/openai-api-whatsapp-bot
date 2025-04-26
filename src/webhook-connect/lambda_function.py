import os

def lambda_handler(event, context):
    token = os.environ['META_WPP_WEBHOOK_TOKEN']

    print("EVENTO RECEBIDO:", event)

    params = event.get("queryStringParameters", {})

    print('hub.mode: ', params.get("hub.mode"))
    print('verify_token: ', params.get("hub.verify_token"))

    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == token:
        challenge = int(params.get("hub.challenge"))
        print('challenge: ', challenge)
        return {
              "statusCode": 200,
              "body": challenge
          }
    else:
        return {
            "statusCode": 403,
            "body": "Token inválido"
        }