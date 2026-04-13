import asyncio
import json

import websockets


async def main():
    uri = "ws://127.0.0.1:8088/search/document"

    async with websockets.connect(uri) as websocket:
        #await websocket.send("90a380df-9284-47bb-9b24-66bdcb679f8e:qual é o objetivo principal deste documento?")
        await websocket.send("90a380df-9284-47bb-9b24-66bdcb679f8e:Quais as atividades prevista para o primeiro mes?")
        response = await websocket.recv()
        if(response):
            response = json.loads(response)
            print(f"Resposta: {response.get('answer','')}")
        else:
            print("Sem resposta")


if __name__ == "__main__":
    asyncio.run(main())