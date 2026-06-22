import json

from core import get_dotenv_values
from redis_service import RedisService

if __name__ == '__main__':
    values = get_dotenv_values()
    print("Iniciando servico")
    redis_service = RedisService(values)
    print("Servico iniciado")