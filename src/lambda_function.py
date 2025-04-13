import requests
from openai import OpenAI
import json
import os

def lambda_handler(event, context):
    api_key = os.environ['OPENAI_API_KEY']
    wpp_token = os.environ['META_WPP_API_TOKEN']
    wpp_business_phone_id = os.environ['WHATSAPP_BUSINESS_PHONE_NUMBER_ID']

    print(event)

    to = event['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
    received_message = event['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']

    client = OpenAI(api_key=api_key)

    with open(file='src/controle_contexto.json', mode='r', encoding='utf-8') as contexto:
        ctx_inicial_iagen = '\n'.join(json.loads(contexto.read())['contexto_inicial'])
        contexto.close()

    completion = client.chat.completions.create(\
        model="gpt-4o",
        messages=[
            {
                "role": "developer",
                "content": ctx_inicial_iagen
            },
            {
                "role": "user",
                "content": received_message
            }
        ]
    )

    url = f'https://graph.facebook.com/v22.0/{wpp_business_phone_id}/messages'
    headers = {
        'Authorization': f'Bearer {wpp_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {
            'body': completion.choices[0].message.content,
        }
    }

    # Envia a requisição POST com dados no formato JSON
    response = requests.post(url, headers=headers, json=payload)

    return {
        'statusCode': 200,
        'body': 'OK'
    }