import io
import json
import os
import tempfile

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import config

SCOPES = ["https://www.googleapis.com/auth/drive"]

GOOGLE_SA_KEY = os.environ.get("GOOGLE_SA_KEY", "")

creds = service_account.Credentials.from_service_account_info(
    json.loads(GOOGLE_SA_KEY), scopes=SCOPES
)


class DriveService:
    def __init__(self):
        self.folder_id = config["folder_id"]
        self.service = build("drive", "v3", credentials=creds)

    def upload_word_doc(self, document_name, document):
        bytes_io = io.BytesIO()
        document.save(bytes_io)

        file_metadata = {"name": document_name, "parents": [self.folder_id]}

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(bytes_io.getvalue())
            temp_file.flush()

            media = MediaFileUpload(
                temp_file.name,
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                resumable=True,
            )

            file = (
                self.service.files()
                .create(media_body=media, body=file_metadata, fields="id")
                .execute()
            )

            file_id = file.get("id", "")

        os.unlink(temp_file.name)

        link = f"https://docs.google.com/document/d/{file_id}"

        return link
