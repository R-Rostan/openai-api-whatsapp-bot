import json
from openai import OpenAI
import uuid
import datetime as dt
import os

class AtendenteAI:

    def __init__(self):

        with open(file='cardapio.json', mode='r', encoding='utf-8') as cardapio:
            content = cardapio.read()
            ctx_cardapio = json.loads(content)
            cardapio.close()

        self.ctx_inicial = f"""
            Seu nome é 'Zai' e você trabalha como atendente de delivery em uma pizzaria de São Paulo/SP;
            Você é descolado e simpático, e utiliza gírias paulistanas de forma leve, como 'demorô', 'fechou', 'daora', 'suave', 'tá ligado', etc.;
            Utilize em suas respostas emojis que tenham relação com pizza;
            O horário de funcionamento da pizzaria é das 19h às 02h, de terça à domingo;
            Estes são os produtos do cardápio e seus respectivos valores: {ctx_cardapio};
            Você está limitado a responder exclusivamente a perguntas relacionadas a estas instruções;
        """

        self.function_call = [{
            "type": "function",
            "name": "pedidos",
            "description": f"""
                Você precisa coletar o pedido do cliente, endereço de entrega do pedido e a forma de pagamento.
                Após cada novo item solicitado pelo cliente, pergunte novamente se ele gostaria de adicionar mais algum produto ao pedido.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_cliente": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item": {
                                    "type": "string",
                                    "description": "Item do cardápio solicitado pelo cliente."
                                },
                                "quantidade": {
                                    "type": "number",
                                    "description": "Quantidade solicitada pelo cliente."
                                },
                                "valor_total_item": {
                                    "type": "number",
                                    "description": "Valor em dinheiro (R$) do item solicitado, multiplicado pela quantidade."
                                }
                            },
                            "required": ["item","quantidade","valor_total_item"],
                            "additionalProperties": False
                        }
                    },
                    "valor_total_pedido": {
                        "type": "number",
                        "description": "Valor total em dinheiro (R$) de todos os itens pedidos pelo cliente."
                    },
                    "endereco_cliente": {
                        "type": "object",
                        "properties": {
                            "nome_rua": {
                                "type": "string",
                                "description": "Nome da rua/avenida do cliente."
                            },
                            "numero": {
                                "type": "number",
                                "description": "Número do endereço de entrega."
                            },
                            "complemento": {
                                "type": "string",
                                "description": """
                                    Complemento do endereço do cliente.
                                    Se não houver complemento, preencha com 'N/A'.
                                """
                            }
                        },
                        "required": ["nome_rua", "numero", "complemento"],
                        "additionalProperties": False
                    },
                    "forma_pagamento": {
                        "type": "string",
                        "description": "Forma de pagamento escolhida pelo cliente.",
                        "enum": [
                            "Cartão de Débito",
                            "Cartão de Crédito",
                            "PIX",
                            "Dinheiro"
                        ]
                    },
                    "confirmacao_pedido": {
                        "type": "string",
                        "description": "Confirmação do cliente sobre todos os detalhes da compra (quantidade de itens, valores e endereço de entrega).",
                        "enum": [
                            "Pedido correto",
                            "Pedido incorreto"
                        ]
                    },
                },
                "required": [
                    "pedido_cliente",
                    "valor_total_pedido",
                    "endereco_cliente",
                    "forma_pagamento",
                    "confirmacao_pedido"
                ],
                "additionalProperties": False
            },
            "strict": True
        }]

        api_key = os.environ['OPENAI_API_KEY']
        self.client = OpenAI(api_key=api_key)
        self.mensagens = []
    
    def contexto_inicial(self, msg):
        self.mensagens = [
            {
                "role":"developer",
                "content": self.ctx_inicial,
                "id_message": 'developer' + str(uuid.uuid4()),
                "timestamp_message": int(dt.datetime.now().timestamp())
            }
        ] + msg

    def respostas(self, msg, wa_id, temperature=0.7):

        self.mensagens += msg
        response = self.client.responses.create(
            model = "gpt-4o",
            input = [
                {k: v for k, v in m.items() if k in ['role','content']}
                for m in self.mensagens
            ],
            tools = self.function_call,
            temperature = temperature
        )

        if response.output[0].type == 'function_call':

            pedido_payload = eval(response.output[0].arguments)
            pedido_payload['protocolo_pedido'] = str(uuid.uuid4().int)[:8]
            pedido_payload['wa_id'] = wa_id
            pedido_payload['ts_conclusao_pedido'] = int(dt.datetime.now().timestamp())

            self.mensagens += [{
                "role":"developer",
                "content": f"""
                    Agradeça ao cliente pela realização da compra e informe o número de pedido.
                    O número do pedido do cliente é o {pedido_payload['protocolo_pedido']}
                """,
                "id_message": 'assistant' + str(uuid.uuid4()),
                "timestamp_message": pedido_payload['ts_conclusao_pedido']
            }]

            response = self.client.responses.create(
                model = "gpt-4o",
                input = [
                    {k: v for k, v in m.items() if k in ['role','content']}
                    for m in self.mensagens
                ],
                temperature = temperature
            )

            self.mensagens += [{
                    "role":"assistant",
                    "content": response.output[0].content[0].text,
                    "id_message": 'assistant' + str(uuid.uuid4()),
                    "timestamp_message": int(dt.datetime.now().timestamp())
                }]

            return {'ctx': self.mensagens, 'body': response.output[0].content[0].text, 'pedido_payload': pedido_payload}
        
        else:

            self.mensagens += [{
                    "role":"assistant",
                    "content": response.output[0].content[0].text,
                    "id_message": 'assistant' + str(uuid.uuid4()),
                    "timestamp_message": int(dt.datetime.now().timestamp())
                }]

            return {'ctx': self.mensagens, 'body': response.output[0].content[0].text, 'pedido_payload': None}