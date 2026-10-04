
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

url = "http://127.0.0.1:5000/api/readings"

data = {
    "zone_id": 1,
    "consumption_liters": 350
}

request = Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urlopen(request) as response:
        print("Status:", response.status)
        print(response.read().decode("utf-8"))
except HTTPError as error:
    print("Status:", error.code)
    print(error.read().decode("utf-8"))