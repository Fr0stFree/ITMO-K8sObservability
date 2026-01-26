from aiokafka import ConsumerRecord


async def on_new_message(record: ConsumerRecord) -> None:
    print(f"got message: {record.value}")
