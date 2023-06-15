import json
import os
from typing import List, Union

import firebase_admin
from firebase_admin import credentials, firestore

FIRESTORE_SA_KEY = os.environ.get("FIRESTORE_SA_KEY", "")

cred = credentials.Certificate(json.loads(FIRESTORE_SA_KEY))
firebase_admin.initialize_app(cred)


class FirestoreService:
    def __init__(self) -> None:
        self.db = firestore.client()

    def _get_collection(self, path: List[str]):
        ref = self.db
        for i in range(len(path)):
            if i % 2 == 0:
                ref = ref.collection(path[i])
            else:
                ref = ref.document(path[i])
        return ref

    def batch_write(self, instructions: List[dict]) -> None:
        batch = self.db.batch()

        for instruction in instructions:
            path = instruction["path"]
            data = instruction["data"]
            batch.set(self._get_collection(path), data)

        batch.commit()
