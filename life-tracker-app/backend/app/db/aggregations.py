from pymongo.asynchronous.collection import AsyncCollection


async def count_by_day(
    collection: AsyncCollection, date_field: str, start: str, end: str
) -> dict[str, int]:
    """Count documents per calendar day for `YYYY-MM-DD` string dates in [start, end].

    ISO date strings sort lexicographically in date order, so a string range match is correct.
    """
    pipeline = [
        {"$match": {date_field: {"$gte": start, "$lte": end}}},
        {"$group": {"_id": f"${date_field}", "count": {"$sum": 1}}},
    ]
    cursor = await collection.aggregate(pipeline)
    return {row["_id"]: row["count"] async for row in cursor}
