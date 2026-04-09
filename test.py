import asyncio

import websockets


async def main():
    uri = "ws://127.0.0.1:8000/extraction/ocr"

    async with websockets.connect(uri) as websocket:
        await websocket.send("documents:1/f1e4f147-0e55-498a-9ca6-29bd26167ea3.pdf")
        response = await websocket.recv()
        print(f"Resposta: {response}")


if __name__ == "__main__":
    asyncio.run(main())
