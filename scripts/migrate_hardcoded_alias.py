import asyncio
import os

import bootstrap
from dotenv import load_dotenv
from src.activity_utils import normalize_repo_id
from src.alias_service import add_developer_alias

load_dotenv()


async def main():
    repo_id = normalize_repo_id(os.getenv("GITHUB_OWNER"), os.getenv("GITHUB_REPO"))
    await add_developer_alias(repo_id, "YUVRAJ", "YUVRAJ SADANA")
    print(f"Migrated alias YUVRAJ -> YUVRAJ SADANA for repo_id={repo_id}")


if __name__ == "__main__":
    asyncio.run(main())