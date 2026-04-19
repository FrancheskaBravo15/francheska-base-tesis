from database.mongoDb import DatabaseConnection
from models.appointmentModel import AppointmentModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class AppointmentRepository:
    COLLECTION_NAME = "appointments"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, appointment: AppointmentModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(appointment.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear cita en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, appointment_id: str) -> Optional[AppointmentModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(appointment_id)})
            return AppointmentModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar cita por Id en la BD: {e}")
            raise

    @classmethod
    def find_by_client(cls, client_id: str) -> List[AppointmentModel]:
        try:
            collection = cls._get_collection()
            return [AppointmentModel.from_dict(a) for a in
                    collection.find({"client_id": client_id}).sort([("date", -1), ("start_time", -1)])]
        except PyMongoError as e:
            print(f"Error al buscar citas por cliente en la BD: {e}")
            raise

    @classmethod
    def find_by_worker(cls, worker_id: str) -> List[AppointmentModel]:
        try:
            collection = cls._get_collection()
            return [AppointmentModel.from_dict(a) for a in
                    collection.find({"worker_id": worker_id}).sort([("date", -1), ("start_time", 1)])]
        except PyMongoError as e:
            print(f"Error al buscar citas por trabajadora en la BD: {e}")
            raise

    @classmethod
    def find_by_worker_and_date(cls, worker_id: str, date: str) -> List[AppointmentModel]:
        try:
            collection = cls._get_collection()
            return [AppointmentModel.from_dict(a) for a in
                    collection.find({
                        "worker_id": worker_id,
                        "date": date,
                        "status": {"$nin": ["cancelada"]}
                    }).sort("start_time", 1)]
        except PyMongoError as e:
            print(f"Error al buscar citas por trabajadora y fecha en la BD: {e}")
            raise

    @classmethod
    def find_pending_reschedule_by_client(cls, client_id: str) -> List[AppointmentModel]:
        try:
            collection = cls._get_collection()
            return [AppointmentModel.from_dict(a) for a in
                    collection.find({"client_id": client_id, "status": "pendiente_reagenda"})]
        except PyMongoError as e:
            print(f"Error al buscar reagendamientos pendientes en la BD: {e}")
            raise

    @classmethod
    def find_pending_validation(cls) -> List[AppointmentModel]:
        """Citas esperando validación de comprobante por el admin."""
        try:
            collection = cls._get_collection()
            return [AppointmentModel.from_dict(a) for a in
                    collection.find({"status": "pendiente_validacion"}).sort("created_at", 1)]
        except PyMongoError as e:
            print(f"Error al buscar citas pendientes de validación: {e}")
            raise

    @classmethod
    def count_pending_validation(cls) -> int:
        try:
            return cls._get_collection().count_documents({"status": "pendiente_validacion"})
        except PyMongoError:
            return 0

    @classmethod
    def find_by_combo_instance(cls, combo_instance_id: str) -> List[AppointmentModel]:
        try:
            collection = cls._get_collection()
            return [AppointmentModel.from_dict(a) for a in
                    collection.find({"combo_instance_id": combo_instance_id}).sort("start_time", 1)]
        except PyMongoError as e:
            print(f"Error al buscar citas del combo: {e}")
            raise

    @classmethod
    def update_status(cls, appointment_id: str, status: str) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": status}})
        except PyMongoError as e:
            print(f"Error al actualizar estado de cita en la BD: {e}")
            raise

    @classmethod
    def update_status_by_combo_instance(cls, combo_instance_id: str, status: str) -> int:
        try:
            result = cls._get_collection().update_many(
                {"combo_instance_id": combo_instance_id},
                {"$set": {"status": status}}
            )
            return result.modified_count
        except PyMongoError as e:
            print(f"Error al actualizar estado del combo: {e}")
            raise

    @classmethod
    def update_data(cls, appointment_id: str, data: dict) -> None:
        try:
            collection = cls._get_collection()
            set_fields   = {k: v for k, v in data.items() if v is not None}
            unset_fields = {k: "" for k, v in data.items() if v is None}
            update = {}
            if set_fields:
                update["$set"] = set_fields
            if unset_fields:
                update["$unset"] = unset_fields
            if update:
                collection.update_one({"_id": ObjectId(appointment_id)}, update)
        except PyMongoError as e:
            print(f"Error al actualizar datos de cita en la BD: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[AppointmentModel]:
        try:
            collection = cls._get_collection()
            return [AppointmentModel.from_dict(a) for a in
                    collection.find().sort([("date", -1), ("start_time", 1)])]
        except PyMongoError as e:
            print(f"Error al obtener todas las citas en la BD: {e}")
            raise

    @classmethod
    def cancel_by_combo_instance(cls, combo_instance_id: str, client_id: str,
                                  reason: str = "") -> int:
        try:
            collection = cls._get_collection()
            result = collection.update_many(
                {"combo_instance_id": combo_instance_id, "client_id": client_id,
                 "status": {"$nin": ["cancelada"]}},
                {"$set": {"status": "cancelada", "cancel_reason": reason}}
            )
            return result.modified_count
        except PyMongoError as e:
            print(f"Error al cancelar citas del combo: {e}")
            raise

    @classmethod
    def has_conflict(cls, worker_id: str, date: str, start_time: str, end_time: str,
                     exclude_id: str = None) -> bool:
        try:
            collection = cls._get_collection()
            query = {
                "worker_id": worker_id,
                "date": date,
                "status": {"$nin": ["cancelada"]},
                "$and": [
                    {"start_time": {"$lt": end_time}},
                    {"end_time":   {"$gt": start_time}}
                ]
            }
            if exclude_id:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            return collection.find_one(query) is not None
        except PyMongoError as e:
            print(f"Error al verificar conflicto de cita en la BD: {e}")
            raise
