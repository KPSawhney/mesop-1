(lsof -t -i:32123 | xargs kill) || true && \
bazel run //mesop-1/cli -- --path=mesop-1/genai/index.py --prod
