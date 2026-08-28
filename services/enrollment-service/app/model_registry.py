from abc import ABC, abstractmethod

class ModelRegistry(ABC):
    @abstractmethod
    def get_embedding_model_info(self) -> dict: ...

class StubModelRegistry(ModelRegistry):
    def get_embedding_model_info(self) -> dict:
        return {"model_name": "stub-model", "version": 1}
