#!/usr/bin/env python3
"""Minimal Flask test to debug startup issues"""

from flask import Flask
import sys

print("[1] Creating Flask app...", flush=True)
app = Flask(__name__)

print("[2] Setting secret key...", flush=True)
import secrets
app.secret_key = secrets.token_hex(32)

print("[3] Creating route...", flush=True)
@app.route('/')
def hello():
    return "Hello World"

print("[4] Flask app ready, starting server...", flush=True)
sys.stdout.flush()

if __name__ == '__main__':
    print("[5] Calling app.run()...", flush=True)
    sys.stdout.flush()
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
