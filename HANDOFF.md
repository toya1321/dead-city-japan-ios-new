# 引き継ぎメモ（v149.22 時点、2026-11-18）

新しいセッションでは「ブランチ `claude/blissful-fermat-8e7k1b-u8y7jb` の HANDOFF.md から続けて」と伝える。

## リポジトリの構成

- ゲーム本体はリポジトリに直接置いていない。`ci/v149.10-source/part-*`（30分割のzip、sha256 `36a2f709…9158`）を元に、`ci/` のパッチを順に当てて作る。
- 適用順（すべて `git apply --directory=game`）：
  1. `v149.10-ios-build` 2. `v149.11-local-ai` 3. `v149.11-comparison` 4. `v149.16-npc-dialogue` 5. `v149.17-npc-retry` 6. `v149.18-npc-requests` 7. `v149.19-npc-shopping` 8. `v149.20-npc-reasons` 9. `v149.21-ui` 10. `v149.22-chips-scroll` 11. `v149.23-wip-photos` 12. `v149.24-wip-walkers`（作業中：ゾンビ。`scripts/walkers.gd`）（作業中：写真の追加。画像がそろったら版を上げて正式なパッチにする。バイナリを含むので `git diff --binary` で作る）
- 新しい版は「直前の版を当てた状態」との差分を `ci/v149.NN-<名前>.patch` として追加する。版番号は `export_presets.cfg`（short_version / version）と `build_scripts/build-ios-unsigned.sh`（アサートとIPA名）、`scripts/title_screen.gd` の表記を上げる。現在 0.149.22 / ビルド171。
- 各版の説明はパッチ内の `NPC_UPDATE_v149.*.md`、`UI_UPDATE_v149.*.md`、`verification/V149_18_REAL_MODEL.md`。

## 作業環境の作り方（Linux）

```bash
cat ci/v149.10-source/part-* > game.zip && unzip -q game.zip -d game
cd game && git init -q && git add -A && git commit -qm base   # 差分作成用
for p in v149.10-ios-build v149.11-local-ai v149.11-comparison v149.16-npc-dialogue v149.17-npc-retry v149.18-npc-requests v149.19-npc-shopping v149.20-npc-reasons v149.21-ui v149.22-chips-scroll; do git apply ../ci/$p.patch; done
```

- Godot 4.6.3（`Godot_v4.6.3-stable_linux.x86_64`、GitHub releases から取得可）。`mkdir -p build && touch build/.gdignore` → `godot --headless --path . --import --quit`。
- 全テスト：`GODOT=<godot> python3 tests/run_all.py build/test-results`（現在136/136、約12分）。
- 画面の撮影：`xvfb-run -a godot --path . --rendering-driver opengl3 --resolution 390x844 --script res://qa/<撮影スクリプト>.gd`（Xvfbはコンテナにある）。

## 実モデル（Qwen3-4B）での会話テスト

- llama.cpp：GitHub のアーカイブはこの環境から取得できない。`pip download --no-deps --no-binary :all: llama-cpp-python==0.3.37` の同梱版（`vendor/llama.cpp`、API一致を確認済み）を使う。
- プローブ：`cmake -S build_scripts/local_llm -B probe -DLLAMA_SOURCE=<vendor/llama.cpp> -DGGML_NATIVE=ON && cmake --build probe`。
- モデル：Hugging Face はこの環境から届かない。`mirror.gcr.io/v2/ai/qwen3/blobs/sha256:336228a2…`（4B-F16、約8GB）を取得し、同じllama.cppの `llama-quantize … Q4_K_M` で変換（約2.5GB）。
- 実行：`DCJ_LLAMA_PROBE=<probe>/dcj_local_llm_probe DCJ_GGUF=<gguf> [DCJ_SCENARIOS=chat,shopping_vague] godot --headless --path . --script res://qa/real_npc_scenarios.gd`。1ターン十数秒〜1分（CPU）。結果はJSON行（返答・出所・却下文・状態変化）。

## IPAのビルド（GitHub Actions、macOS）

- ワークフローは `.github/workflows/ios-native-v149NN.yml`。**ゲームのパッチを push しただけではビルドしない**（ユーザーの希望）。ワークフローファイル自体を追加・変更した時と、手動実行（Actions → Run workflow）の時だけ動く。
- GitHubは一度も動いていないワークフローを手動実行できない（404）。新しい版は「前の版のワークフローをコピーしてパッチ行を1行足したファイル」を追加して push すると、それがビルドの開始になる。
- 完成すると Artifacts に `DeadCityJapan-v149.NN-local-llm-unsigned`（約62MB）。ユーザーは SideStore で入れる。所要約9分。
- 2026-11-17夜（JST）に macOS ランナーが割り当てられず約15分でキャンセルされる現象があった（翌朝は正常）。再発したら時間を置いて再実行。Codemagic 用の `codemagic.yaml`（手動開始）もあるが、ユーザーの登録は途中（メールの確認コード待ち）。
- リポジトリは公開。標準ランナーは無料。

## 実機のAI

- iPhoneの「ファイル」→ このiPhone内 → DeadCityJapan → `Models/Qwen3-4B-Q4_K_M.gguf`（または `Qwen3-1.7B-Q4_K_M.gguf`）。ユーザーは4Bを使用中。応答時間は問題なしとの報告。

## これまでの主な変更（v149.17〜v149.22）

- v149.17：繰り返しの再生成で却下文を引用しない。
- v149.18：自由な言い方の依頼を、短い判定呼び出し＋ゲームの決まった処理で実行（買い物・料理・寝る・映画・水・食事・ニュース・扉・鍵・同行・取り消し）。否定や無関係な判定は実行しない。
- v149.19：1回の外出で最大4品の買い物。「10個ずつ」「水と食料」。注文と時間をモデルの事実に渡す。
- v149.20：買い物の上限の理由を事実に渡す。崩れた文（数字＋小さい仮名）を作り直す。
- v149.21：UIの作り直し（上部の帯、吹き出しの記録、会話の帯、候補ボタン、写真の折りたたみ、タブ式メニュー、図の地図、設定の整理）。外に出る時に鍵を自動で開ける。
- v149.22：候補ボタンを横スワイプしても押されないようにした。

UIのモックアップ：https://claude.ai/artifact/Q1ZFHfhgNSeXFaJm3MxBpk（6画面）。

## 次にやること（ユーザーと合意した順）

1. **ゾンビとの遭遇**（v149.24-wip で第一段階を実装済み：起き上がり・場所ごとの数・1時間ごとの移動と音・遭遇（隠れる/逃げる/戦う/様子を見る）・噛まれると約3日で死亡（失敗の多くは引っかき傷で、噛まれるのは近くでつかまれた時だけ。死んだら生きている同居人が主人公を引き継ぐ）・ヘッダーの感染者数と候補ボタン・セーブ。最初の感染者は住民id7。同居人との遭遇（つかまれるのが同居人のこともある、一緒に逃げる）、同居人が噛まれた時の「隔離する／看病する」、約3日で死亡、死んだ部屋で起き上がる、隔離した部屋を開けると遭遇。テスト `test_walkers149_24`（34項目）。全137テスト合格。未実装：自宅への侵入、ニュース・防災無線、実モデルでの遭遇中の自由文、施設の中の移動。方向はユーザーと合意済み：ゆっくり歩く・噛まれたら数日で助からない・戦えるが基本は避ける。設計は `ZOMBIE_DESIGN.md`）：死者が起き上がる、歩き回る・音や光に寄る・群れる、遭遇時の隠れる・逃げる・戦う（時間・音・体力・ケガ・噛まれる危険のコスト）、噛まれた後の進行。あわせて序盤の時間の進み方（今は2週間ほど何も起きない、初期食料が2人で2日半）。現状、住民48人は画面外で死ぬだけで、街は無人になる。
2. （作業中）ユーザーがChatGPTで画像を作成中。商店通りの4状態（`shopping_street.jpg` と `_alert` / `_collapse` / `_overgrown`）を追加済み。写真は `<名前>_<段階>.jpg` があれば街の段階（`main.gd::_visual_phase`）に合わせて自動で切り替わる。次に頼んでいる画像：住宅街 `residential.jpg`、駅前 `station_front.jpg`（それぞれ4状態）、ほかの外の場所の状態ちがい。1440×810に縮小し、Godotで `--import` して `.import` も含める（既存の `.import` を消さないこと）。
3. 場所をデータで追加できるようにする（病院・ドラッグストア・スーパー・ホームセンター・学校・警察・ガソリンスタンド等）。ユーザーがChatGPTで画像を作成中。画像は場所ごとに normal / alert / collapse / overgrown の4状態をそろえると今の仕組みにそのまま入る。
4. プレイヤーの自由行動の読み取り（v149.18の依頼と同じ「AIは意図だけ、成否はゲームの規則」方式を行動全体へ）。物ごとの用途（包丁＝武器・料理、板＋釘＋金づち＝窓を塞ぐ）。
5. 外の生存者NPCと関係性（信頼・恩・裏切り・役割分担）。
6. 拠点の運営（入口ごとの守り、明かりと音、仲間の仕事）と、生き延びることの深さ（ケガ・病気・寒さ・心の状態）。

## ユーザーについて

- 日本語でやりとりする。時刻は日本時間で伝える。
- 進めるたびに実機で確かめたい。ビルドは頼まれた時だけ行う。
- iPhoneで遊んで、スクショで報告してくれる。
