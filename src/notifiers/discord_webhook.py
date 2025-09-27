import os, json, requests

def send_discord_message(text: str):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return
    payload = {"content": text[:1900]}
    requests.post(url, headers={"Content-Type":"application/json"}, data=json.dumps(payload))
