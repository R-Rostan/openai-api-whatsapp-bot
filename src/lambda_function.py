import requests
from openai import OpenAI
import json
import os
import boto3
import uuid
import datetime as dt
import atendente_ai

def lambda_handler(event, context):
    
    wpp_token = os.environ['META_WPP_API_TOKEN']
    wpp_business_phone_id = os.environ['WHATSAPP_BUSINESS_PHONE_NUMBER_ID']
    
    dynamo_table = 'wpp-chat'
    dynamo = boto3.client('dynamodb', region_name='us-east-1')
    
    zai = atendente_ai.AtendenteAI()
 
    msg_check = event['entry'][0]['changes'][0]['value'].get('statuses')
    if msg_check is not None:      
        
        status_mensagem = msg_check[0]['status']
        ts_status_mensagem = msg_check[0]['timestamp']
    
    else:
        
        print('payload_recebido:', event)

        wa_id = event['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
        received_message = event['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        id_message = event['entry'][0]['changes'][0]['value']['messages'][0]['id']
        timestamp_message = event['entry'][0]['changes'][0]['value']['messages'][0]['timestamp']
        
        ctx_check = dynamo.get_item(TableName=dynamo_table, Key={'wa_id':{'S': wa_id}}).get('Item')

        if ctx_check is not None:

            msg = eval(ctx_check['contexto']['S'])
            msg += [
                {
                    "role": "user",
                    "content": received_message,
                    "id_message": id_message,
                    "timestamp_message": timestamp_message
                }
            ]

        else:

            msg = [{
                "role": "user",
                "content": received_message,
                "id_message": id_message,
                "timestamp_message": timestamp_message
            }]

            zai.contexto_inicial(msg = msg)

        mensagens = zai.respostas(msg = msg, wa_id = wa_id)

        dynamo_add_item = dynamo.put_item(
            TableName = dynamo_table,
            Item = {
                'wa_id':{'S': wa_id},
                'contexto':{'S': str(mensagens['ctx'])}
            }
        )

        url = f'https://graph.facebook.com/v22.0/{wpp_business_phone_id}/messages'
        headers = {
            'Authorization': f'Bearer {wpp_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'messaging_product': 'whatsapp',
            'to': wa_id,
            'type': 'text',
            'text': {
                'body': mensagens['body'],
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if mensagens['pedido_payload'] != None:

            s3 = boto3.client('s3')
            bucket_name = 'rr-raw-data'

            # Raw pedidos
            anomesdia = dt.datetime.now().strftime('%Y%m%d')
            nome_arquivo = anomesdia + '-' + str(uuid.uuid4())
            s3_key = f'raw-wpp-pedidos/anomesdia={anomesdia}/{nome_arquivo}.json'
            json_payload = json.dumps(mensagens['pedido_payload'])

            s3.put_object(
                Bucket = bucket_name,
                Key = s3_key,
                Body = json_payload,
                ContentType = 'application/json'
            )

            # Delete conversa em aberto
            dynamo.delete_item(TableName=dynamo_table, Key={'wa_id':{'S': wa_id}})

    return {
        'statusCode': 200,
        'body': 'OK'
    }