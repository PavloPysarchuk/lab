#!/bin/bash
# RETIRED: the RTX 4060 is reserved for the production voice worker. Everything runs on the 4090 via run_gpu0.sh.
exec "$(dirname "$0")/run_gpu0.sh" "$@"
