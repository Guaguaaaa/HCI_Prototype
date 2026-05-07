import sys

import data_manager


def main():
    target = "production"
    if len(sys.argv) > 1:
        target = sys.argv[1].strip().lower()

    if target not in {"production", "test"}:
        raise SystemExit("Usage: python backend/clear_database.py [production|test]")

    deleted = data_manager.clear_database_contents(target)
    print(f"Cleared {target} database:")
    for name, count in deleted.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
