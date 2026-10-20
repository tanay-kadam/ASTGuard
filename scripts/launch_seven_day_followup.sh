#!/usr/bin/env bash
set -eu
cd /tmp/astguard_seven_day_20261012
tmux new-session -d -s astguard_7day_monitor -c /tmp/astguard_seven_day_20261012 \
  /home/tkadam/ASTGuard/.venv/bin/python -u scripts/seven_day_finalize.py --monitor
for gpu in 0 1 2 3 4 5 6 7; do
  tmux new-session -d -s "astguard_7day_eval_g${gpu}" -c /tmp/astguard_seven_day_20261012 \
    /home/tkadam/ASTGuard/.venv/bin/python -u scripts/seven_day_finalize.py --gpu "$gpu"
done
