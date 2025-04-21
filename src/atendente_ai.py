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
                Você precisa coletar o pedido do cliente e o endereço de entrega do pedido.
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
                    "confirmacao_pedido": {
                        "type": "string",
                        "description": """
                            Se o cliente confirma que estão corretos todos os detalhes da compra (quantidade de itens, valores e endereço de entrega), preencha com 'Sim'.
                            Caso contrário, preencha com 'Não'.
                        """
                    },
                },
                "required": ["pedido_cliente", "valor_total_pedido", "endereco_cliente", "confirmacao_pedido"],
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

    def respostas(self, msg, temperature=0.7):

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

            print('Pedido completo.')
            print(response.output[0].arguments)

            self.mensagens += [{
                "role":"developer",
                "content": "Agradeça ao cliente pela realização do pedido.",
                "id_message": 'assistant' + str(uuid.uuid4()),
                "timestamp_message": int(dt.datetime.now().timestamp())
            }]

            response = self.client.responses.create(
                model = "gpt-4o",
                input = [
                    {k: v for k, v in m.items() if k in ['role','content']}
                    for m in self.mensagens
                ],
                temperature = temperature
            )

            print(response.output[0].content[0].text)
        
        else:

            print(response.output[0].content[0].text)

        self.mensagens += [{
                "role":"assistant",
                "content": response.output[0].content[0].text,
                "id_message": 'assistant' + str(uuid.uuid4()),
                "timestamp_message": int(dt.datetime.now().timestamp())
            }]

        return {'ctx': self.mensagens, 'body': response.output[0].content[0].text}