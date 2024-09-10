from pymongo import MongoClient, ReturnDocument
from bson.objectid import ObjectId
from google.protobuf import empty_pb2, field_mask_pb2
import user_pb2
from user_pb2 import User
from abc import ABC, abstractmethod

class UserDAO(ABC):
    @abstractmethod
    def create_user(self, name, email, location=None) -> User:
        pass

    @abstractmethod
    def get_user(self, id) -> User:
        pass

    @abstractmethod
    def update_user(self, user, update_mask) -> User:
        pass

    @abstractmethod
    def delete_user(self, id) -> None:
        pass

class UserDAOMongoDB(UserDAO):
    def __init__(self, uri="mongodb://mongodb:27017/", db_name="user", collection_name="users"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _from_mongo(self, doc):
        location = doc.get('location')
        if location is not None:
            location = user_pb2.Geolocation(
                latitude=location.get('latitude', 0),
                longitude=location.get('longitude', 0)
            )
        doc['location'] = location
        doc['id'] = str(doc['_id'])
        del doc['_id']
        return User(**doc)

    def _to_mongo(self, user):
        doc = {
            "name": user.name,
            "email": user.email,
        }
        if user.location is not None:
            doc['location'] = {
                "latitude": user.location.latitude,
                "longitude": user.location.longitude
            }
        return doc

    def create_user(self, name, email, location=None) -> User:
        user = User(name=name, email=email, location=location)
        result = self.collection.insert_one(self._to_mongo(user))
        user.id = str(result.inserted_id)
        return user

    def get_user(self, id) -> User:
        doc = self.collection.find_one({"_id": ObjectId(id)})
        if doc:
            return self._from_mongo(doc)
        return None

    def update_user(self, user, update_mask) -> User:
        update_fields = self._to_mongo(user)
        for field in set(update_fields.keys()) - set(update_mask.paths):
            del update_fields[field]

        updated_doc = self.collection.find_one_and_update(
            {"_id": ObjectId(user.id)},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )
        if updated_doc:
            return self._from_mongo(updated_doc)
        return None

    def delete_user(self, id) -> None:
        self.collection.delete_one({"_id": ObjectId(id)})
