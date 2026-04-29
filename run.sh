#!/usr/bin/env bash
set -e

cd /home/danglingbo/okex_web
uvicorn app:app --host 0.0.0.0 --port 8008 --no-access-log --log-level error