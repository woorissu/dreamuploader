import json

with open("sample_config/naebu.json", encoding="utf-8") as f:
    config = json.load(f)

print("표시용 이름:", config.get("display_name"))
print("사진 수:", len(config.get("photos", [])))

