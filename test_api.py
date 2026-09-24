import requests

BASE_URL = "https://kokkai.ndl.go.jp/api/speech"

params = {
    "any": "消費税",
    "nameOfMeeting": "本会議",
    "maximumRecords": 3,
    "recordPacking": "json",
}

resp = requests.get(BASE_URL, params=params)
resp.raise_for_status()
data = resp.json()

print("総件数:", data.get("numberOfRecords"))
print("返戻件数:", data.get("numberOfReturn"))
print("---")

for rec in data.get("speechRecord", []):
    print(rec["date"], rec["nameOfHouse"], rec["nameOfMeeting"], "/", rec["speaker"], rec.get("speakerGroup"))
    print(rec["speech"][:100], "...")
    print("---")
