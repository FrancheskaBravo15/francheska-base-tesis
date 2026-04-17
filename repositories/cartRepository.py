from database.mongoDb import DatabaseConnection
from models.cartModel import CartModel, CartItemModel
from typing import Optional
from pymongo.errors import PyMongoError

class CartRepository:
    COLLECTION_NAME = "carts"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional[CartModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"user_id": user_id})
            return CartModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar carrito por user_id en la BD: {e}")
            raise

    @classmethod
    def upsert(cls, cart: CartModel) -> None:
        """Crea o actualiza el carrito del usuario."""
        try:
            collection = cls._get_collection()
            collection.update_one(
                {"user_id": cart.user_id},
                {"$set": cart.to_dict()},
                upsert=True
            )
        except PyMongoError as e:
            print(f"Error al guardar carrito en la BD: {e}")
            raise

    @classmethod
    def clear(cls, user_id: str) -> None:
        """Vacía el carrito del usuario."""
        try:
            collection = cls._get_collection()
            collection.update_one(
                {"user_id": user_id},
                {"$set": {"items": []}}
            )
        except PyMongoError as e:
            print(f"Error al vaciar carrito en la BD: {e}")
            raise
