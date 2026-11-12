"""Estimate planned or observed Jev input cost without reading credentials."""
import argparse
import json
from pathlib import Path

PRICE_PER_MILLION_INPUT_TOKENS = 0.042


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=200)
    parser.add_argument("--tokens-per-case", type=float)
    parser.add_argument("--log", type=Path, help="Append-only Jev JSONL call log")
    args = parser.parse_args()
    if args.log:
        rows = [json.loads(line) for line in args.log.read_text().splitlines() if line.strip()]
        tokens = sum((row.get("usage") or {}).get("input_tokens", 0) for row in rows)
        print(json.dumps({"records": len(rows), "input_tokens": tokens,
                          "estimated_usd": tokens * PRICE_PER_MILLION_INPUT_TOKENS / 1_000_000}))
        return
    if args.tokens_per_case is None or args.tokens_per_case < 0 or args.cases < 0:
        parser.error("provide non-negative --tokens-per-case, or --log")
    tokens = args.cases * args.tokens_per_case
    print(json.dumps({"cases": args.cases, "tokens_per_case": args.tokens_per_case,
                      "input_tokens": tokens,
                      "estimated_usd": tokens * PRICE_PER_MILLION_INPUT_TOKENS / 1_000_000}))


if __name__ == "__main__":
    main()
