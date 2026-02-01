from collections.abc import Iterable

from opentelemetry.context import Context
from opentelemetry.propagate import extract as extract_context
from opentelemetry.propagators.textmap import Getter


# TODO: fix
class KafkaContextExtractor(Getter):
    def get(self, carrier: Iterable[tuple[str, bytes]], key: str) -> list[str] | None:
        values = [value.decode("utf-8") for header_key, value in carrier if header_key.lower() == key.lower()]
        return values or None

    def keys(self, carrier: Iterable[tuple[str, bytes]]) -> list[str]:
        return [key for key, _ in carrier]

    def extract(self, carrier: Iterable[tuple[str, bytes]]) -> Context:
        return extract_context(carrier, getter=self)
