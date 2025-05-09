import pandas as pd
import boto3
import io
import json
import datetime as dt
import uuid
import urllib.parse

def lambda_handler(event, context):
    
    file = urllib.parse.unquote(event['Records'][0]['s3']['object']['key'])

    s3 = boto3.client('s3')

    response = s3.get_object(Bucket = 'rr-raw-data', Key = file)
    content = response['Body'].read().decode('utf-8')
    json_data = json.loads(content)

    df_dados_unicos = pd.DataFrame([{
        k: v for k, v in json_data.items() 
        if k in ['valor_total_pedido',
                 'forma_pagamento',
                 'confirmacao_pedido',
                 'protocolo_pedido',
                 'wa_id',
                 'ts_conclusao_pedido']
    }])

    df_pedido = pd.DataFrame(json_data['pedido_cliente'])
    df_pedido['protocolo_pedido'] = json_data['protocolo_pedido']

    df_endereco = pd.DataFrame([json_data['endereco_cliente']])
    df_endereco['protocolo_pedido'] = json_data['protocolo_pedido']

    ord_col = [
        'protocolo_pedido',
        'valor_total_pedido',
        'wa_id',
        'ts_conclusao_pedido',
        'item',
        'quantidade',
        'valor_total_item',
        'forma_pagamento',
        'confirmacao_pedido',
        'nome_rua',
        'numero',
        'complemento'
    ]

    df = df_dados_unicos\
        .merge(right=df_pedido, how='left', on='protocolo_pedido')\
        .merge(right=df_endereco, how='left', on='protocolo_pedido')

    df = df[ord_col]

    df = df.astype({
        'protocolo_pedido': 'int64',
        'valor_total_pedido': 'float64',
        'wa_id': 'string',
        'ts_conclusao_pedido': 'int64',
        'item': 'string',
        'quantidade': 'int64',
        'valor_total_item': 'float64',
        'forma_pagamento': 'string',
        'confirmacao_pedido': 'string',
        'nome_rua': 'string',
        'numero': 'int64',
        'complemento': 'string'
    })

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine='pyarrow')

    anomesdia = dt.datetime.now().strftime('%Y%m%d')
    nome_arquivo = anomesdia + '-' + str(uuid.uuid4())
    
    bucket_name = 'rr-curated-data'
    s3_key = f'curated-wpp-pedidos/anomesdia={anomesdia}/{nome_arquivo}.parquet'

    buffer.seek(0)
    s3.put_object(
        Bucket = bucket_name,
        Key = s3_key,
        Body = buffer
    )

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }