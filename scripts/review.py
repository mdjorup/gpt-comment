import json
import os

import firebase_admin
from firebase_admin import credentials

FIRESTORE_SA_KEY = os.environ.get("FIRESTORE_SA_KEY", "")

cred = credentials.Certificate(json.loads(FIRESTORE_SA_KEY))
firebase_admin.initialize_app(cred)


def get_unreviewed_essays():
    return
