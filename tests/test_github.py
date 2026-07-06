import asyncio

import bootstrap
from src.github_service import fetch_commits

async def main():
    result = await fetch_commits("sadanayuvraj09-commits", "revenue_detective_test")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
