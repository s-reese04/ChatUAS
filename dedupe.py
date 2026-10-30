import json

seen = set()
kept = 0
removed = 0

with open("chunks.jsonl", encoding="utf-8") as src, \
     open("chunks_clean.jsonl", "w", encoding="utf-8") as dst:
    for line in src:
        record = json.loads(line)
        if record["text"] in seen:
            removed += 1
            continue
        seen.add(record["text"])
        dst.write(line)
        kept += 1

print(kept, "kept,", removed, "removed")