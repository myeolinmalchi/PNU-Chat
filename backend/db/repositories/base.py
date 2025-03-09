from contextlib import contextmanager
from functools import wraps
import logging
from typing import Callable, Dict, Generic, Tuple, Type, TypeVar, Any, List
from sqlalchemy.orm import Query, Session
from db.common import Base, get_session, session_context_var
from abc import abstractmethod

logger = logging.getLogger(__name__)


class TransactionalMetaclass(type):
    """
    Metaclass that automatically applies transactional decorator to repository methods.
    """

    def __new__(cls, name: str, bases: tuple, attrs: Dict[str, Any]) -> Type:
        # Existing transactional logic
        cls.apply_transactional_wrapper(attrs)

        # Create the new class
        new_class = super().__new__(cls, name, bases, attrs)

        # Set the model attribute
        cls.set_model_attribute(new_class, bases)

        return new_class

    @classmethod
    def apply_transactional_wrapper(cls, attrs: Dict[str, Any]) -> None:
        transactional_prefixes = (
            "find", "search", "get", "create", "update", "delete", "upsert"
        )

        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and any(attr_name.startswith(prefix)
                                            for prefix in transactional_prefixes
                                            ):
                attrs[attr_name] = cls.add_transactional(attr_value)

    @staticmethod
    def add_transactional(method: Callable) -> Callable:
        if hasattr(method, "_transactional"):
            return method

        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return transactional(method)(*args, **kwargs)

        wrapper.__setattr__("_transactional", True)
        return wrapper

    @staticmethod
    def set_model_attribute(new_class: Type, bases: Tuple[Type, ...]) -> None:
        if bases and any(base.__name__ == "BaseRepository" for base in bases):
            if hasattr(new_class, "__orig_bases__"):
                model_type = new_class.__orig_bases__[0].__args__[0]
                if not hasattr(new_class, "model") or new_class.model is None:
                    new_class.model = model_type


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType], metaclass=TransactionalMetaclass):

    model = None

    @property
    def session(self) -> Session:
        return session_context_var.get()

    def create(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance

    def bulk_create(self, objects: List[ModelType]) -> List[ModelType]:
        self.session.bulk_save_objects(objects)
        self.session.flush()
        return objects

    def create_all(self, objects: List[ModelType]) -> List[ModelType]:
        self.session.add_all(objects)
        self.session.flush()
        return objects

    def expunge_all(self):
        """Explicitly remove all objects from the current session."""
        try:
            self.session.expunge_all()
            logger.info(f"All objects expunged from session {id(self.session)}")
        except Exception as e:
            logger.error(f"Error during expunge_all: {str(e)}")
            raise

    def upsert(
        self,
        new: ModelType,
        query: Query[ModelType],
        columns: List[str] = []
    ) -> ModelType:
        prev = query.one_or_none()
        if prev is None:
            self.session.add(new)
            return new

        columns = [col for col in columns if col in new.keys()]
        for col in columns:
            value = getattr(new, col)
            setattr(prev, col, value)

        self.session.flush()

        return prev

    @abstractmethod
    def upsert_all(self, objects: List[ModelType]) -> List[ModelType]:
        pass

    def update(self, instance: ModelType, data: Dict[str, Any]) -> ModelType:
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
            else:
                raise AttributeError(
                    f"{type(instance).__name__} has no attribute '{key}'"
                )

        self.session.flush()
        return instance

    def update_all(
        self, instances: List[ModelType], datas: List[Dict[str, Any]]
    ):
        for instance, data in zip(instances, datas):
            self.update(instance, data)

    def delete(self, data: ModelType) -> None:
        self.session.delete(data)
        self.session.flush()


@contextmanager
def transaction():
    session = session_context_var.get()
    if session is None:
        session = get_session()
        session_context_var.set(session)

    # Check if there's already an active transaction
    is_nested = session.in_transaction()
    savepoint = session.begin_nested() if is_nested else None
    try:
        if is_nested:
            assert savepoint
            logger.debug("Starting nested transaction")

            yield savepoint

            savepoint.commit()
            logger.debug("Savepoint committed")
        else:
            # Start a new transaction
            session.begin()
            logger.debug("Starting new transaction")

            yield session

            session.commit()
            session.close()
            logger.debug("Transaction committed")

    except Exception as e:
        logger.exception(
            "Exception occurred during transaction, rolling back", exc_info=e
        )
        if is_nested:
            assert savepoint
            savepoint.rollback()
            logger.debug("Savepoint rolled back")
        else:
            session.rollback()
            session.close()
            logger.debug("Transaction rolled back")
        raise
    finally:
        if not is_nested:
            session_context_var.set(None)


def transactional(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        with transaction():
            return func(*args, **kwargs)

    return wrapper
