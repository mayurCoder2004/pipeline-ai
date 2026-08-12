import asyncio
import json

from redis_client import get_value_redis
from integrations.hubspot import get_items_hubspot


async def main():
    credentials = await get_value_redis(
        "hubspot_credentials:TestOrg:TestUser"
    )

    if not credentials:
        print("No HubSpot credentials found in Redis.")
        return

    # Redis returns bytes, so decode them first.
    if isinstance(credentials, bytes):
        credentials = credentials.decode("utf-8")

    # Convert JSON string into Python dictionary.
    if isinstance(credentials, str):
        credentials = json.loads(credentials)

    items = await get_items_hubspot(credentials)

    print("\n========================================")
    print("HubSpot Integration Items")
    print("========================================")

    for item in items:
        print("\nID:", item.id)
        print("Type:", item.type)
        print("Name:", item.name)
        print("Created:", item.creation_time)
        print("Modified:", item.last_modified_time)
        print("URL:", item.url)

    print("\n========================================")
    print("Total Items:", len(items))
    print("========================================")


if __name__ == "__main__":
    asyncio.run(main())