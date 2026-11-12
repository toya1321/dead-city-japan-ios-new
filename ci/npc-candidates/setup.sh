set -euo pipefail
archive="$RUNNER_TEMP/deadcity.zip"
cat ci/v149.10-source/part-* > "$archive"
printf '%s  %s\n' 36a2f709df872c42ed478b826816b12c34f79cd8ddaa8416711d6a37d76a9158 "$archive" | shasum -a 256 -c -
unzip -q "$archive" -d game
for patch in v149.10-ios-build v149.11-local-ai v149.11-comparison v149.12-dialogue v149.12-conversation-qa v149.13-qwen35; do
  git apply --directory=game "ci/$patch.patch"
done
git apply --directory=game ci/npc-candidates/probe.patch
curl -fLsS --retry 3 https://github.com/ggml-org/llama.cpp/archive/refs/tags/b12247.tar.gz -o "$RUNNER_TEMP/llama.tar.gz"
tar -xzf "$RUNNER_TEMP/llama.tar.gz" -C "$RUNNER_TEMP"
cmake -S game/build_scripts/local_llm -B "$RUNNER_TEMP/probe" -DCMAKE_BUILD_TYPE=Release -DLLAMA_SOURCE="$RUNNER_TEMP/llama.cpp-b12247"
cmake --build "$RUNNER_TEMP/probe" --parallel 4
