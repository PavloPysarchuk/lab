#!/bin/bash
# Alias: everything runs on the RTX 4090 via run_gpu0.sh (the 4060 is off limits).
exec "$(dirname "$0")/run_gpu0.sh" "$@"
