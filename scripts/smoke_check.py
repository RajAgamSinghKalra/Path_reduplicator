import json
import argparse
from app.deduper import check_duplicate


def main(path: str):
    with open(path, encoding='utf-8') as f:
        payload = json.load(f)
    result = check_duplicate(payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a duplicate check from a JSON payload")
    parser.add_argument("payload", help="Path to JSON file containing customer fields")
    args = parser.parse_args()
    main(args.payload)
