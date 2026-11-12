import csv
import json
import os
from pathlib import Path
import subprocess
import sys

binary, model = sys.argv[1:]
production = Path("game/scripts/local_npc_model.gd").read_text().split('const CHAT_INSTRUCTIONS := """')[1].split('"""')[0]
short_json = '日常の質問に日本語で直接、1〜2文で答えてください。出力は {"kind":"chat","value":"回答"} のJSONのみ。'
plain = '日常の質問に日本語で直接、1〜2文で答えてください。'
cases = [
    ("color", "青と紫が混ざった色って何色？", "どんな気分になる？", "青と紫が混ざった色は、静かな気分になるね。そんな色を見ると心がほっとするの。"),
    ("arithmetic", "17足す28はいくつ？", "暗算は得意？", "簡単な足し算ならできるよ。"),
    ("capital", "フランスの首都はどこ？", "旅行するならどこに行きたい？", "フランスに行ってみたいな。"),
    ("translation", "英語で猫は何て言う？", "猫は好き？", "うん、猫は好きだよ。"),
    ("opposite", "「暑い」の反対は？", "夏と冬どっちが好き？", "冬かな。暖かい部屋で過ごすのが好き。"),
    ("sequence", "月曜日の次の日は何曜日？", "月曜日はどうだった？", "ゆっくり過ごせたよ。"),
]
modes = ("plain", "json", "game_question", "persona", "history")
inputs = []
labels = []
for i, mode in enumerate(modes):
    for name, question, previous, reply in cases[i:] + cases[:i]:
        data = {"spoken_by_player": question}
        if mode in ("persona", "history"):
            data |= {"name":"詩音", "place":"居間", "time":"09:10", "first_person":"私",
                     "speaking_style":"穏やかに話す", "condition":"元気", "personality":"穏やかで聞き上手",
                     "activity":"在宅", "relationship":"同居人。一緒に観終えた映画: ロッキー",
                     "recent_dialogue":[]}
        if mode == "history":
            data["recent_dialogue"] = [{"player":previous,"reply":reply}]
        prompt = plain if mode == "plain" else short_json if mode == "json" else production
        payload = question if mode in ("plain", "json") else json.dumps(data, ensure_ascii=False, sort_keys=True)
        inputs.extend([payload, "plain" if mode == "plain" else "json", "\v".join(prompt.splitlines())])
        labels.append((mode, name))
Path("results").mkdir(exist_ok=True)
env = os.environ | {"DCJ_ACCURACY_MATRIX":"1"}
with open("results/backend.log", "w") as backend:
    proc = subprocess.run([binary, model, "/dev/null"], input="\n".join(inputs)+"\n",
                          text=True, stdout=subprocess.PIPE, stderr=backend, env=env, timeout=1800)
rows = list(csv.reader(proc.stdout.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE))
assert len(rows) == len(labels), (proc.returncode, len(rows), len(labels))
with open("results/answers.jsonl", "w") as result:
    for (mode, case), row in zip(labels, rows, strict=True):
        load, first, elapsed, prompt_count, cache, output_count, peak, device, error, answer = row
        record = {"condition":mode, "case":case, "load_ms":int(load), "first_ms":int(first),
                  "total_ms":int(elapsed), "prompt_tokens":int(prompt_count), "cached":int(cache),
                  "output_tokens":int(output_count), "peak_bytes":int(peak), "backend":device,
                  "status":error, "answer":answer}
        line = json.dumps(record, ensure_ascii=False)
        print("DCJ_EVAL " + line)
        result.write(line+"\n")
