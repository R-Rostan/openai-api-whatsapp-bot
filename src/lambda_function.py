import requests
from openai import OpenAI
import json
import os
import boto3
import uuid
import datetime as dt

def lambda_handler(event, context):
    api_key = os.environ['OPENAI_API_KEY']
    wpp_token = os.environ['META_WPP_API_TOKEN']
    wpp_business_phone_id = os.environ['WHATSAPP_BUSINESS_PHONE_NUMBER_ID']
    dynamo_table = 'wpp-chat'

    print('payload_recebido:', event)
 
    msg_check = event['entry'][0]['changes'][0]['value'].get('statuses')
    if msg_check is not None:      
        
        status_mensagem = msg_check[0]['status']
        ts_status_mensagem = msg_check[0]['timestamp']
        print(f'status: {status_mensagem}, timestamp: {ts_status_mensagem}')
    
    else:

        to = event['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
        received_message = event['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        id_message = event['entry'][0]['changes'][0]['value']['messages'][0]['id']
        timestamp_message = event['entry'][0]['changes'][0]['value']['messages'][0]['timestamp']

        with open(file='controle_contexto.json', mode='r', encoding='utf-8') as contexto:
            ctx_inicial_iagen = ';'.join(json.loads(contexto.read())['contexto_inicial'])
            contexto.close()

        dynamo = boto3.client('dynamodb', region_name='us-east-1')
        
        ctx_check = dynamo.get_item(TableName=dynamo_table, Key={'wa_id':{'S': to}}).get('Item')
        if ctx_check is not None:

            messages = eval(ctx_check['contexto']['S'])
            messages += [
                {
                    "role": "user",
                    "content": received_message,
                    "id_message": id_message,
                    "timestamp_message": timestamp_message
                }
            ]

        else:

            messages = [
                {
                    "role": "developer",
                    "content": ctx_inicial_iagen,
                    "id_message": 'developer' + str(uuid.uuid4()),
                    "timestamp_message": int(dt.datetime.now().timestamp())
                },
                {
                    "role": "user",
                    "content": received_message,
                    "id_message": id_message,
                    "timestamp_message": timestamp_message
                }
            ]

        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {k: v for k, v in m.items() if k in ['role','content']}
                for m in messages
            ]
        )
        resposta = completion.choices[0].message.content

        messages += [
            {
                "role": "assistant",
                "content": resposta,
                "id_message": 'assistant' + str(uuid.uuid4()),
                "timestamp_message": int(dt.datetime.now().timestamp())
            }
        ]

        dynamo_add_item = dynamo.put_item(
            TableName = dynamo_table,
            Item = {
                'wa_id':{'S': to},
                'contexto':{'S': str(messages)}
            }
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
                'body': resposta,
            }
        }

        response = requests.post(url, headers=headers, json=payload)

    return {
        'statusCode': 200,
        'body': 'OK'
    }