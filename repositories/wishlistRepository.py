from database.mongoDb import DatabaseConnection
from models.wishlistModel import WishlistModel
from typing import Optional
from pymongo.errors import PyMongoError

class WishlistRepository:
    COLLECTION_NAME = "wishlists"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional[WishlistModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"user_id": user_id})
            return WishlistModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar wishlist en la BD: {e}")
            raise

    @classmethod
    def upsert(cls, wishlist: WishlistModel) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one(
                {"user_id": wishlist.user_id},
                {"$set": wishlist.to_dict()},
                upsert=True
            )
        except PyMongoError as e:
            print(f"Error al guardar wishlist en la BD: {e}")
            raise
