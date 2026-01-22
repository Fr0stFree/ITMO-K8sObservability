from concurrent import futures
import grpc

from protocol import greeter_pb2, greeter_pb2_grpc


class GreeterService(greeter_pb2_grpc.GreeterServiceServicer):

    def SayHello(self, request, context):
        return greeter_pb2.HelloReply(
            message=f"Hello, {request.name}!"
        )


def serve() -> None:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    greeter_pb2_grpc.add_GreeterServiceServicer_to_server(
        GreeterService(),
        server,
    )

    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()