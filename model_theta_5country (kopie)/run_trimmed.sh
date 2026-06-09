#!/usr/bin/env bash
# ============================================================================
#  run_trimmed.sh — minimal run that answers ONE question with error bars:
#  "across the convergence parameter lambda, does relationship banking ever
#   RAISE the relationship country's output (vs an all-transaction control)?"
#
#  It is the lambda sweep (config + control at each lambda), at NSEEDS=12.
#  lambda=0.3 is the anchor and is included. ~96 runs total.
#
#  RUN FROM INSIDE model_theta_5country/ (the folder with timing.py):
#     cp run_trimmed.sh analyze.py model_theta_5country/
#     cd model_theta_5country
#     chmod +x run_trimmed.sh
#     caffeinate -i ./run_trimmed.sh      # ~1 hour on an M1 Air (4 perf cores)
#     python3 analyze.py                  # read the "E2 LAMBDA SWEEP" section
#
#  Tunables (env): NSEEDS (default 12), NCORES (default = perf cores), LAMBDAS.
# ============================================================================
set -u

NSEEDS=${NSEEDS:-12}
NCORES=${NCORES:-$(sysctl -n hw.perflevel0.logicalcpu 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)}
NCYCLE=${NCYCLE:-300}
LAMBDAS=${LAMBDAS:-"1.0 0.5 0.3 0.1"}     # the sweep (0.3 = anchor)
RUNDIR=${RUNDIR:-./runs}
LOGDIR=${LOGDIR:-./logs}
TH="THETA_ON=1 THETA_SPREAD=0.5 SELF_NOISE=0.1 GAP_KAPPA=0.5"

[ -f timing.py ] || { echo "ERROR: run from inside the model folder (no timing.py here)"; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
mkdir -p "$RUNDIR" "$LOGDIR"

NRUNS=$(( $(echo $LAMBDAS | wc -w) * 2 * NSEEDS ))
echo "cores=$NCORES  seeds/config=$NSEEDS  lambdas=[$LAMBDAS]  total_runs=$NRUNS"
echo "(check cores=4 above; if it says 8, Ctrl-C and rerun: NCORES=4 caffeinate -i ./run_trimmed.sh)"

SEEDS=$(seq 0 $((NSEEDS-1)))
sem () { while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$NCORES" ]; do sleep 2; done; }
launch () {  # TAG ENVSTR SEED
  local tag="$1" envs="$2" seed="$3"
  sem
  ( env $envs OUTPUT_BASE="$RUNDIR/${tag}_s${seed}_" CONFIG_TAG="$tag" \
        NCYCLE="$NCYCLE" FIRSTRUN="$seed" LASTRUN="$seed" python3 timing.py \
        > "$LOGDIR/${tag}_s${seed}.log" 2>&1 ) &
}

for L in $LAMBDAS; do
  t=$(echo "$L" | tr -d '.')                 # 0.3 -> 03 (tag-safe; matches analyze.py)
  echo ">> lambda=$L"
  for s in $SEEDS; do
    launch "E2_rel_L$t"  "RB_C0=1 $TH LAMBDA_INN=$L" "$s"   # relationship country 0 + theta
    launch "E2_ctrl_L$t" "$TH LAMBDA_INN=$L"          "$s"  # all-transaction control
  done
done
wait
echo "DONE. ${NRUNS} runs in $RUNDIR/ . Now run:  python3 analyze.py"
echo "Look at the 'E2 LAMBDA SWEEP' table: a '+' output line with a '*' (CI excludes 0)"
echo "would mean relationship banking RAISES the relationship country's output."
