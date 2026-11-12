import json
import os
from pathlib import Path
import subprocess
import sys

binary, model = sys.argv[1:]
production = Path("game/scripts/local_npc_model.gd").read_text().split('const CHAT_INSTRUCTIONS := """')[1].split('"""')[0]
focused = ('日本の生活ゲームの同居人として、プレイヤーの最後の発言に自然な日本語で1〜2文で答える。'
           '日常知識の質問は結論から。共有した出来事は資料にあるものだけを使う。口調は資料に合わせる。'
           '返答は {"kind":"chat","value":"台詞"} のJSONのみ。')
cases = [
    ("color", "青と紫が混ざった色って何色？", "どんな気分になる？", "青と紫が混ざった色は、静かな気分になるね。"),
    ("translation", "猫って英語で何て言う？", "猫は好き？", "好きだよ。よく日なたにいるよね。"),
    ("arithmetic", "17足す28はいくつ？", "暗算得意？", "簡単な計算ならね。"),
    ("capital", "フランスの首都はどこ？", "昨日の映画面白かったね", "練習の場面が印象的だったよ。"),
    ("opposite", "「暑い」の反対は？", "昨日の映画面白かったね", "練習の場面が印象的だったよ。"),
    ("sequence", "月曜日の次の日は何曜日？", "何曜日が好き？", "金曜日かな。"),
    ("memory", "この前一緒に観た映画の題名、覚えてる？", "前に一緒に映画観たよね", "練習の場面が印象に残ってるよ。"),
    ("chat", "なんか暇だね。家でできる遊びを一つ提案して", "フランスの首都はどこ？", "パリだよ。"),
]
Path("results").mkdir(exist_ok=True)
for seed in (42, 73):
    inputs, labels = [], []
    for condition in ("current", "focused"):
        for name, question, previous, reply in cases:
            data = {"spoken_by_player": question, "speaking_style":"穏やかで親しみやすい"}
            if condition == "current":
                data |= {"name":"詩音", "place":"居間", "time":"09:10", "first_person":"私",
                         "condition":"元気", "personality":"穏やかで聞き上手", "activity":"在宅",
                         "relationship":"同居人。一緒に観終えた映画: ロッキー",
                         "recent_dialogue":[{"player":previous,"reply":reply}]}
            if name == "memory":
                data["recent_memories"] = ["一緒に観終えた映画: ロッキー。練習の場面が印象に残った。"]
            prompt = production if condition == "current" else focused
            inputs.extend([json.dumps(data, ensure_ascii=False, sort_keys=True), "json", "\v".join(prompt.splitlines())])
            labels.append((condition, name))
    env = os.environ | {"DCJ_ACCURACY_MATRIX":"1", "DCJ_EVAL_SEED":str(seed)}
    with open(f"results/backend-{seed}.log", "w") as backend:
        proc = subprocess.run([binary, model, "/dev/null"], input="\n".join(inputs)+"\n",
                              text=True, stdout=subprocess.PIPE, stderr=backend, env=env, timeout=1250)
    rows = [line.split("\t", 9) for line in proc.stdout.splitlines()]
    assert len(rows) == len(labels), (proc.returncode, len(rows), len(labels), proc.stdout[-500:])
    with open(f"results/answers-{seed}.jsonl", "w") as result:
        for (condition, name), row in zip(labels, rows, strict=True):
            _, first, elapsed, tokens, cache, count, peak, device, status, raw = row
            try:
                parsed = json.loads(raw)
            except ValueError:
                parsed = {}
            item = {"condition":condition, "case":name, "seed":seed, "first_ms":int(first), "total_ms":int(elapsed),
                    "prompt_tokens":int(tokens), "cached":int(cache), "output_tokens":int(count), "peak_bytes":int(peak),
                    "backend":device, "status":status, "kind":parsed.get("kind"), "answer":parsed.get("value", raw)}
            line = json.dumps(item, ensure_ascii=False)
            print("DCJ_COMPARE " + line, flush=True)
            result.write(line+"\n")
