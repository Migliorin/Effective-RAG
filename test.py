import argparse
import asyncio
import json

import websockets


async def main(uri: str, document_id: str, question: str) -> None:
    message = f"{document_id}:{question}"

    async with websockets.connect(uri) as websocket:
        await websocket.send(message)
        response = await websocket.recv()

        if response:
            try:
                response_data = json.loads(response)
                print(f"Resposta: {response_data.get('answer', '')}")
            except json.JSONDecodeError:
                print("Resposta recebida não é um JSON válido:")
                print(response)
        else:
            print("Sem resposta")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cliente WebSocket para consulta de documentos."
    )

    parser.add_argument(
        "--uri",
        default="ws://127.0.0.1:8088/search/document",
        help="URI do servidor WebSocket",
    )

    parser.add_argument(
        "--document-id",
        required=True,
        help="ID do documento",
    )

    parser.add_argument(
        "--question",
        required=True,
        help="Pergunta a ser enviada",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.uri, args.document_id, args.question))
