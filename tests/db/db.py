import asyncio
from tests.db.dummy import init_db_with_dummy
from tests.db.gemini import init_db_with_gemini
from tests.db.utils import drop_views_and_tables


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "teardown":
        asyncio.run(drop_views_and_tables())
    elif len(sys.argv) > 1 and sys.argv[1] == "setup-dummy":
        asyncio.run(init_db_with_dummy())
    elif len(sys.argv) > 1 and sys.argv[1] == "setup-gemini":
        asyncio.run(init_db_with_gemini())
    else:
        print("Error: Please specify 'setup-dummy', 'setup-gemini', or 'teardown'")
        print("Usage: python -m tests.db.db setup-dummy|setup-gemini|teardown")
        sys.exit(1)
