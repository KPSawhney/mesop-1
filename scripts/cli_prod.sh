(lsof -t -i:32123 | xargs kill) || true && \
bazel run //genai/cli -- --path=mesop-1/genai/index.py
