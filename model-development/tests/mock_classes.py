import torch
class NamespaceStats:
    def __init__(self, vector_count):
        self.vector_count = vector_count

class DummyStats:
    def __init__(self):
        self.dimension = 384
        self.index_fullness = 0.0
        self.metric = "cosine"
        self.namespaces = {
            "namespace1": NamespaceStats(10000),
            "namespace2": NamespaceStats(300),
        }
        self.total_vector_count = 10300
        self.vector_type = "dense"



class DummyFetchResponse:
    def __init__(self, namespace, ids):

        self.namespace = namespace
        if isinstance(ids, dict):  # If IDs contain metadata, use it directly
            self.vectors = {id_: DummyVector(id_, metadata) for id_, metadata in ids.items()}
        elif isinstance(ids, list):  # If only IDs, create dummy objects
            self.vectors = {id_: DummyVector(id_) for id_ in ids}
        else:
            self.vectors = {}

    def to_dict(self):
        return {"namespace": self.namespace, "vectors": {id_: v.to_dict() for id_, v in self.vectors.items()}}

class DummyVector:
    def __init__(self, id_, metadata = None):
        self.id = id_
        self.metadata = metadata if metadata is not None else {'key':'value'}
        self.values = []

    def to_dict(self):
        return {"id": self.id, "metadata": self.metadata, "values": self.values}

