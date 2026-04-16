from dotenv import dotenv_values


def get_dotenv_values() -> dict:
    return {**dotenv_values(".env")}
