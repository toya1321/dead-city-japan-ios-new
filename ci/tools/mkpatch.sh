#!/bin/bash
# Regenerate ci/v149.35-world.patch (code/text) + ci/v149.35-assets (images), verify, report.
set -e
S=/tmp/w/scratch; mkdir -p $S
R=/home/claude/dead-city-japan-ios-new
cd /tmp/w/game2
B=$(git -C ../g18 rev-parse HEAD)
git add -A . ':!build' ':!.godot' 2>/dev/null || true
git diff --cached --name-status --diff-filter=AM $B -- . ':!build' ':!.godot' | awk '$2 ~ /\.(jpg|png|webp|jpeg)$/ {print $2}' > $S/imgs.txt
EXC=$(sed 's/^/:!/' $S/imgs.txt | tr '\n' ' ')
git diff --cached --binary $B -- . ':!build' ':!.godot' $EXC > $R/ci/v149.35-world.patch
rm -rf $R/ci/v149.35-assets/assets; mkdir -p $R/ci/v149.35-assets
while read f; do mkdir -p "$R/ci/v149.35-assets/$(dirname "$f")"; cp "$f" "$R/ci/v149.35-assets/$f"; done < $S/imgs.txt
rm -rf $S/verify; cp -r ../g18 $S/verify; (cd $S/verify && git apply $R/ci/v149.35-world.patch && cp -R $R/ci/v149.35-assets/assets/. assets/)
diff -rq --exclude=.git --exclude=build --exclude=.godot . $S/verify && echo "VERIFY OK $(stat -c %s $R/ci/v149.35-world.patch) bytes, $(wc -l < $S/imgs.txt) images"
