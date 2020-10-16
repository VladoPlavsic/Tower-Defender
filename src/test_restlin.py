from fastapi.testclient import TestClient
from Restlin import app

client = TestClient(app)


def test_read_main():
    response = client.put(
        "/tower", json={"message": "Vlado", "tower": "Hocus", "sender": ""})
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    test_read_main()
