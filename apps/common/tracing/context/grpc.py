from grpc.aio import UnaryUnaryClientInterceptor
from opentelemetry.propagate import inject


class OpenTelemetryClientInterceptor(UnaryUnaryClientInterceptor):
    async def intercept_unary_unary(
        self,
        continuation,
        client_call_details,
        request,
    ):
        metadata = []
        if client_call_details.metadata:
            metadata = list(client_call_details.metadata)

        carrier = {}
        inject(carrier)

        for k, v in carrier.items():
            metadata.append((k, v))

        new_details = client_call_details._replace(metadata=metadata)
        return await continuation(new_details, request)
