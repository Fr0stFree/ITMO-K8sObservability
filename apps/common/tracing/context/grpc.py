from grpc.aio import ServerInterceptor, UnaryUnaryClientInterceptor
from opentelemetry import context, propagate


class OpenTelemetryClientInterceptor(UnaryUnaryClientInterceptor):
    async def intercept_unary_unary(self, continuation, client_call_details, request):
        metadata = []
        if client_call_details.metadata:
            metadata = list(client_call_details.metadata)

        carrier = {}
        propagate.inject(carrier)

        for k, v in carrier.items():
            metadata.append((k, v))

        new_details = client_call_details._replace(metadata=metadata)
        return await continuation(new_details, request)


# TODO: fix!!!
class OpenTelemetryServerInterceptor(ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)

        carrier = {}
        for k, v in metadata.items():
            carrier[k] = v

        ctx = propagate.extract(carrier)
        context.attach(ctx)
        return await continuation(handler_call_details)
