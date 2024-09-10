import unittest
from unittest.mock import patch
import grpc
from google.protobuf import empty_pb2, field_mask_pb2
from concurrent import futures
import user_pb2
import user_pb2_grpc
from server import UserServiceServicer
import mongomock

class UserServiceTest(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('dao.user_dao.MongoClient', new=mongomock.MongoClient)
        self.mock_mongo_client = self.patcher.start()

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.servicer = UserServiceServicer()
        user_pb2_grpc.add_UserServiceServicer_to_server(self.servicer, self.server)
        self.server.add_insecure_port('[::]:50051')
        self.server.start()
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = user_pb2_grpc.UserServiceStub(self.channel)

    def tearDown(self):
        self.server.stop(None)
        self.patcher.stop()

    def test_create_user_success(self):
        request = user_pb2.CreateUserRequest(
            name='John Doe',
            email='john.doe@example.com',
            location=user_pb2.Geolocation(latitude=37.7749, longitude=-122.4194)
        )

        response = self.stub.CreateUser(request)
        self.assertEqual(response.name, 'John Doe')
        self.assertEqual(response.email, 'john.doe@example.com')
        self.assertEqual(response.location.latitude, 37.7749)
        self.assertEqual(response.location.longitude, -122.4194)

    def test_get_user_success(self):
        create_request = user_pb2.CreateUserRequest(
            name='John Doe',
            email='john.doe@example.com',
            location=user_pb2.Geolocation(latitude=37.7749, longitude=-122.4194)
        )
        create_response = self.stub.CreateUser(create_request)
        user_id = create_response.id

        get_request = user_pb2.GetUserRequest(id=user_id)
        response = self.stub.GetUser(get_request)
        self.assertEqual(response.id, user_id)
        self.assertEqual(response.name, 'John Doe')
        self.assertEqual(response.email, 'john.doe@example.com')
        self.assertEqual(response.location.latitude, 37.7749)
        self.assertEqual(response.location.longitude, -122.4194)

    def test_update_user_success(self):
        create_request = user_pb2.CreateUserRequest(
            name='John Doe',
            email='john.doe@example.com',
            location=user_pb2.Geolocation(latitude=37.7749, longitude=-122.4194)
        )
        create_response = self.stub.CreateUser(create_request)
        user_id = create_response.id

        update_request = user_pb2.UpdateUserRequest(
            user=user_pb2.User(
                id=user_id,
                name='John Updated',
                email='john.updated@example.com',
                location=user_pb2.Geolocation(latitude=37.7749, longitude=-122.4194)
            ),
            update_mask=field_mask_pb2.FieldMask(paths=['name', 'email'])
        )

        response = self.stub.UpdateUser(update_request)
        self.assertEqual(response.name, 'John Updated')
        self.assertEqual(response.email, 'john.updated@example.com')

    def test_delete_user_success(self):
        create_request = user_pb2.CreateUserRequest(
            name='John Doe',
            email='john.doe@example.com',
            location=user_pb2.Geolocation(latitude=37.7749, longitude=-122.4194)
        )
        create_response = self.stub.CreateUser(create_request)
        user_id = create_response.id

        delete_request = user_pb2.DeleteUserRequest(id=user_id)
        response = self.stub.DeleteUser(delete_request)
        self.assertEqual(response, empty_pb2.Empty())

        get_request = user_pb2.GetUserRequest(id=user_id)
        with self.assertRaises(grpc.RpcError) as context:
            self.stub.GetUser(get_request)
        self.assertEqual(context.exception.code(), grpc.StatusCode.NOT_FOUND)

if __name__ == '__main__':
    unittest.main()
