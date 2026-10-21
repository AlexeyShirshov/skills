#!/usr/bin/env bash
# End-to-end test for the zen-failover plugin.
#
# Two mock subscription providers (Go on 18081, ChatGPT on 18083) answer HTTP
# 429, a mock "direct" provider (18082) streams a valid completion. Scenarios:
#   1. fresh Go limit  -> two 429s, then agents/session/default switch, retry lands
#                         on the fallback
#   2. new process     -> persisted state routes the first request to the fallback
#   3. continued ses   -> the switched session stays on the fallback
#   4. fresh ChatGPT   -> the openai-style rule switches to its own fallback
#   5. transient 429   -> a quota-only source is retried, not switched
#   6. plan is back    -> the startup probe restores the original bindings
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
TEST=/tmp/opencode/zen-failover-test
PLUGIN="${ZEN_FAILOVER_PLUGIN:-$(cd "$ROOT/.." && pwd)}"

pkill -f "zen-failover/mock.py" 2>/dev/null || true
fuser -k 18081/tcp 18082/tcp 18083/tcp 2>/dev/null || true
rm -rf "$TEST"
mkdir -p "$TEST/config/opencode" "$TEST/data" "$TEST/state" "$TEST/cache"
sed "s|__PLUGIN__|$PLUGIN|g" "$ROOT/config.template.jsonc" > "$TEST/config/opencode/opencode.jsonc"

MOCK_LOG="$TEST/mock.jsonl" MOCK_FLIP="$TEST/flip" python3 "$ROOT/mock.py" &
MOCK_PID=$!
trap 'kill "$MOCK_PID" 2>/dev/null || true' EXIT
sleep 0.6

run() {
  local prompt="$1"
  shift
  ( cd "$TEST" && env \
      -u OPENCODE_CONFIG -u OPENCODE_CONFIG_CONTENT -u OPENCODE -u OPENCODE_SESSION_ID \
      -u AI_AGENT -u OPENCODE_TERMINAL \
      XDG_CONFIG_HOME="$TEST/config" XDG_DATA_HOME="$TEST/data" \
      XDG_STATE_HOME="$TEST/state" XDG_CACHE_HOME="$TEST/cache" \
      ZEN_FAILOVER_RULES="mockgo=mockds/deepseek-flash;mockai=mockds/<id>" \
      ZEN_FAILOVER_QUOTA_ONLY="mockai" \
      ZEN_FAILOVER_PROBE_MS="${ZEN_FAILOVER_PROBE_MS:-600000}" \
      ZEN_FAILOVER_PROBE_ON_START="${ZEN_FAILOVER_PROBE_ON_START:-0}" \
      ZEN_FAILOVER_LOG="$TEST/plugin.log" \
      timeout 120 opencode run --standalone --auto --format json "$@" "$prompt" )
}

hits() { grep -c "\"port\": $1," "$TEST/mock.jsonl" 2>/dev/null || true; }
# Per-model hits: the small_model (titles) also goes to the fallback port, so a
# bare port count cannot prove that *Sol* moved.
hits_model() {
  grep "\"port\": $1," "$TEST/mock.jsonl" 2>/dev/null | grep -c "\"model\": \"$2\"" || true
}

echo "== 1. fresh limit =="
: > "$TEST/mock.jsonl"
: > "$TEST/plugin.log"
run "t1: trigger the limit" > "$TEST/t1.out"
grep -q "switched " "$TEST/plugin.log" || { echo "FAIL: no switch"; exit 1; }
grep -q "switchModel " "$TEST/plugin.log" || { echo "FAIL: session not switched"; exit 1; }
[ "$(hits 18081)" -ge 1 ] || { echo "FAIL: no Go request"; exit 1; }
[ "$(hits 18082)" -ge 1 ] || { echo "FAIL: no fallback request"; exit 1; }
grep -q "OK-FALLBACK" "$TEST/t1.out" || { echo "FAIL: wrong answer"; exit 1; }
echo "   ok: Go 429 -> agents + session switched -> fallback answered"

echo "== 2. new process, degraded state =="
: > "$TEST/mock.jsonl"
run "t2: restart while degraded" > "$TEST/t2.out"
grep -q "resumed degraded state" "$TEST/plugin.log" || { echo "FAIL: state not resumed"; exit 1; }
[ "$(hits 18081)" -eq 0 ] || { echo "FAIL: hit Go after restart"; exit 1; }
[ "$(hits 18082)" -ge 1 ] || { echo "FAIL: no fallback request"; exit 1; }
echo "   ok: first request went straight to the fallback"

echo "== 3. continued session =="
: > "$TEST/mock.jsonl"
run "t3: continue the switched session" -c > "$TEST/t3.out"
[ "$(hits 18081)" -eq 0 ] || { echo "FAIL: continued session hit Go"; exit 1; }
[ "$(hits 18082)" -ge 1 ] || { echo "FAIL: no fallback request"; exit 1; }
echo "   ok: continued session stayed on the fallback"

echo "== 4. fresh ChatGPT-style limit =="
rm -rf "$TEST/data" "$TEST/state" "$TEST/cache"
mkdir -p "$TEST/data" "$TEST/state" "$TEST/cache"
: > "$TEST/mock.jsonl"
: > "$TEST/plugin.log"
run "t4: chatgpt quota" --model mockai/sol > "$TEST/t4.out"
grep -q "limit hit: mockai" "$TEST/plugin.log" || { echo "FAIL: mockai not degraded"; exit 1; }
grep -q "switchModel " "$TEST/plugin.log" || { echo "FAIL: chatgpt session not switched"; exit 1; }
[ "$(hits 18083)" -ge 1 ] || { echo "FAIL: no ChatGPT request"; exit 1; }
[ "$(hits_model 18082 sol)" -ge 1 ] || { echo "FAIL: no fallback request for Sol"; exit 1; }
[ "$(hits 18081)" -eq 0 ] || { echo "FAIL: Go hit during ChatGPT scenario"; exit 1; }
grep -q "OK-FALLBACK" "$TEST/t4.out" || { echo "FAIL: wrong answer"; exit 1; }
echo "   ok: ChatGPT 429 -> switched to its fallback, Go untouched"

echo "== 5. transient 429 on a quota-only source =="
rm -rf "$TEST/data" "$TEST/state" "$TEST/cache"
mkdir -p "$TEST/data" "$TEST/state" "$TEST/cache"
: > "$TEST/mock.jsonl"
: > "$TEST/plugin.log"
set +e
run "t5: transient rate limit" --model mockai/sol > "$TEST/t5.out" 2>&1
set -e
if grep -q "limit hit: mockai" "$TEST/plugin.log"; then
  echo "FAIL: transient 429 degraded a quota-only source"; exit 1
fi
[ "$(hits 18083)" -ge 1 ] || { echo "FAIL: no ChatGPT request"; exit 1; }
[ "$(hits_model 18082 sol)" -eq 0 ] || { echo "FAIL: fallback used on a transient 429"; exit 1; }
echo "   ok: transient 429 retried without switching"

echo "== 6. probe restores once the subscription is back =="
rm -rf "$TEST/data" "$TEST/state" "$TEST/cache"
mkdir -p "$TEST/data" "$TEST/state" "$TEST/cache"
rm -f "$TEST/flip"
: > "$TEST/mock.jsonl"
: > "$TEST/plugin.log"
run "t6a: exhaust chatgpt" --model mockai/sol > "$TEST/t6a.out"
grep -q "limit hit: mockai" "$TEST/plugin.log" || { echo "FAIL: mockai not degraded"; exit 1; }
touch "$TEST/flip"
: > "$TEST/mock.jsonl"
: > "$TEST/plugin.log"
ZEN_FAILOVER_PROBE_ON_START=1 run "t6b: restart while degraded" -c > "$TEST/t6b.out"
grep -q "probe mockai: available, restored" "$TEST/plugin.log" || {
  echo "FAIL: the startup probe did not restore mockai"; exit 1
}
# The turn already in flight may still finish on the fallback; the next one must
# be served by the subscription again.
: > "$TEST/mock.jsonl"
run "t6c: next turn after the restore" -c > "$TEST/t6c.out"
[ "$(hits_model 18083 sol)" -ge 1 ] || { echo "FAIL: restored session never reached the subscription"; exit 1; }
[ "$(hits_model 18082 sol)" -eq 0 ] || { echo "FAIL: still routed to the fallback"; exit 1; }
grep -q "OK-PRIMARY" "$TEST/t6c.out" || { echo "FAIL: wrong answer after restore"; exit 1; }
echo "   ok: probe found the plan available and restored the bindings"

echo
echo "PASS: zen-failover end-to-end"
