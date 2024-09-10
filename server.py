import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection
import user_pb2
import user_pb2_grpc
from google.protobuf import empty_pb2, field_mask_pb2
from dao.user_dao import UserDAOMongoDB

SERVICE_NAME = 'UserService'
SERVICE_PORT = '50051'

class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.dao = UserDAOMongoDB()

    def CreateUser(self, request, context):
        user = self.dao.create_user(request.name, request.email, request.location)
        return user

    def GetUser(self, request, context):
        user = self.dao.get_user(request.id)
        if not user:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('User not found')
            return user_pb2.User()
        return user

    def UpdateUser(self, request, context):
        updated_user = self.dao.update_user(request.user, request.update_mask)
        if not updated_user:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('User not found')
            return user_pb2.User()
        return updated_user

    def DeleteUser(self, request, context):
        self.dao.delete_user(request.id)
        return empty_pb2.Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    SERVICE_NAMES = (
        user_pb2.DESCRIPTOR.services_by_name[SERVICE_NAME].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    server.add_insecure_port(f'[::]:{SERVICE_PORT}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    print(f"Serving {SERVICE_NAME} on gRPC on port {SERVICE_PORT} !!!")
    serve()
