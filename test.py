import asyncio

import websockets


async def main():
    uri = "ws://127.0.0.1:8088/extraction/ocr"

    async with websockets.connect(uri) as websocket:
        #await websocket.send("documents:1/811131b0-67ff-443e-89fb-4b956a7fb2b6.pdf")
        await websocket.send("documents:1/90a380df-9284-47bb-9b24-66bdcb679f8e.pdf")
        response = await websocket.recv()
        print(f"Resposta: {response}")


if __name__ == "__main__":
    asyncio.run(main())
