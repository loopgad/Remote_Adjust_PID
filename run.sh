#!/bin/bash
# Start param_id_gui application
# Usage: ./run.sh

cd "$(dirname "$0")"
.venv/bin/python -m param_id_gui "$@"
