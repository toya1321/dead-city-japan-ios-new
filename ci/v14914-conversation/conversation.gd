extends SceneTree
## Integration harness for the real llama.cpp executable. The app on iOS uses
## the same inference core through its static singleton, without a subprocess.
const Main = preload("res://main.tscn")

class RealModel extends RefCounted:
	var executable := OS.get_environment("DCJ_LLAMA_PROBE")
	var model := OS.get_environment("DCJ_GGUF")
	var process := -1
	var raw := ""
	var last_input: Dictionary = {}
	var requests := 0
	var last_system := ""
	var work := ProjectSettings.globalize_path("user://local-llm-smoke")

	func model_available() -> bool:
		return FileAccess.file_exists(executable) and FileAccess.file_exists(model)

	func is_warm() -> bool:
		return false

	func begin(_id: int, instructions: String, input: String) -> bool:
		requests += 1
		last_system = instructions
		last_input = JSON.parse_string(input)
		DirAccess.make_dir_recursive_absolute(work)
		for pair in [["system.txt", instructions], ["input.json", input]]:
			var file := FileAccess.open(work.path_join(pair[0]), FileAccess.WRITE)
			if file == null:
				return false
			file.store_string(pair[1])
			file.close()
		var output := work.path_join("result.json")
		if FileAccess.file_exists(output):
			DirAccess.remove_absolute(output)
		process = OS.create_process(executable, [model, work.path_join("system.txt"), "--request", work.path_join("input.json"), output])
		return process > 0

	func take_result(_id: int) -> String:
		if process < 0 or OS.is_process_running(process):
			return ""
		raw = FileAccess.get_file_as_string(work.path_join("result.json")) if FileAccess.file_exists(work.path_join("result.json")) else "{}"
		process = -1
		return raw

	func cancel(_id: int) -> void:
		if process > 0 and OS.is_process_running(process):
			OS.kill(process)
		process = -1

var failures := 0

func _initialize() -> void:
	call_deferred("run")

func turn(game, backend: RealModel, tag: String, question: String, must_infer: bool, shape: String = "", expected: String = "") -> void:
	var previous := backend.requests
	backend.raw = ""
	var before := Time.get_ticks_msec()
	await game._on_command(question)
	var reply: String = game.log_entries[-1]
	var source: Dictionary = game.last_npc_reply_source
	var inferred := backend.requests > previous
	var focused: bool = inferred and backend.last_system == game.LocalNPCModel.KNOWLEDGE_INSTRUCTIONS
	var prior_turns: Array = backend.last_input.get("recent_dialogue", []) if inferred else []
	var pattern := RegEx.new()
	if not expected.is_empty():
		pattern.compile(expected)
	var match_expected := expected.is_empty() or pattern.search(reply) != null
	var route_ok: bool = inferred == must_infer and (shape != "focused" or focused) and (shape != "context" or not prior_turns.is_empty())
	if not must_infer:
		route_ok = route_ok and source.get("source") in ["game_fact", "game_rule"]
	if not route_ok:
		failures += 1
	print("CONVERSATION ", JSON.stringify({
		"case":tag, "question":question, "reply":reply, "raw":backend.raw,
		"source":source.get("source"), "reason":source.get("reason"), "inferred":inferred,
		"focused":focused, "prior_turns":prior_turns, "expected_match":match_expected,
		"route_ok":route_ok, "ms":Time.get_ticks_msec() - before
	}))

func run() -> void:
	var backend := RealModel.new()
	if not backend.model_available():
		printerr("Missing probe or GGUF")
		quit(2)
		return
	var game = Main.instantiate()
	root.add_child(game)
	await process_frame
	var profile: Dictionary = game.world.DEFAULT_PROFILE.duplicate(true)
	profile.cohabitants = 2
	profile.companion_names = ["詩音", "湊"]
	game._start_new_game(profile)
	game._finish_intro()
	game.location = "居間"
	game._sync_player_position()
	game.world.s.minute = 550
	game.world.s.household_members[0].location = "居間"
	game.world.s.household_members[1].location = "居間"
	game.local_model.backend = backend
	game.local_model.load_timeout_ms = 180000
	game.npc_memory.record(0, 540, "movie", "ロッキー", "練習の場面が印象に残った")
	await turn(game, backend, "small_talk", "詩音、雨の日は家でどう過ごすのが好き？", true)
	await turn(game, backend, "translation_switch", "猫って英語で何て言う？", true, "focused", "(?i)cat|キャット")
	await turn(game, backend, "color", "青と紫が混ざった色って何色？", true, "focused", "青紫|紫青|青み|ブルーパ|バイオレット")
	await turn(game, backend, "follow_up", "それってどういう意味？", true, "context")
	await turn(game, backend, "arithmetic_switch", "17足す28はいくつ？", true, "focused", "45|４５|四十五")
	await turn(game, backend, "why_sky", "夕焼けはなんで赤く見えるの？", true)
	await turn(game, backend, "suggestion", "なんか暇だね。家でできる遊びを一つ提案して", true)
	await turn(game, backend, "memory", "一緒に観た映画覚えてる？", false, "", "ロッキー")
	await turn(game, backend, "other_npc_memory", "湊、一緒に観た映画覚えてる？", false, "", "まだ思い出せない")
	await turn(game, backend, "inventory", "詩音、冷蔵庫に何かあったっけ？", false, "", "品目別")
	await turn(game, backend, "shopping", "ちょっと買い物行ってきて", false, "", "品物と数")
	game.world.s.door_locked = false
	game.world.s.household_members[0].location = "玄関"
	await turn(game, backend, "unclear_action", "詩音、玄関のところを戸締まりお願い", true)
	var locked_before_confirmation: bool = game.world.s.door_locked
	if locked_before_confirmation:
		failures += 1
	var offered: bool = game.pending_local_action.get("key") == "lock_door"
	if offered:
		await game._on_command("提案を実行")
		if not game.world.s.door_locked:
			failures += 1
	print("ACTION ", JSON.stringify({"offered":offered, "locked_before_confirmation":locked_before_confirmation, "locked_after":game.world.s.door_locked}))
	print("CONVERSATION_RESULT ", JSON.stringify({"routing_or_state_failures":failures}))
	quit(0 if failures == 0 else 1)
