import asyncio

import websockets


async def main():
    uri = "ws://127.0.0.1:8000/extraction/ocr"

    async with websockets.connect(uri) as websocket:
        #await websocket.send("documents:1/811131b0-67ff-443e-89fb-4b956a7fb2b6.pdf")
        await websocket.send("documents:1/c168a1e6-b5ec-408e-b0b3-50803cbc253c.pdf")
        response = await websocket.recv()
        print(f"Resposta: {response}")


if __name__ == "__main__":
    asyncio.run(main())
