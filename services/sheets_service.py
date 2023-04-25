import os

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = config["service_account_file"]

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)


class SheetsService:
    def __init__(self):
        self.spreadsheet_id = config["spreadsheet"]["spreadsheet_id"]
        self.sheet_name = config["spreadsheet"]["sheet_name"]
        self.service = build('sheets', 'v4', credentials=creds)

    def get_rows(self):
        result = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f"{self.sheet_name}!A1:Z").execute()
        data = result.get('values', [])
        columns = data[0]
        raw_rows = data[1:]
        rows = []
        for row in raw_rows:
            new_row = row[:len(columns)]
            if len(new_row) < len(columns):
                new_row += [""] * (len(columns) - len(new_row))
            rows.append(new_row)
        df = pd.DataFrame(rows, columns=columns)

        return df
        
    
    def update_cell(self, row : int, column : str, value):
        write_range = f"{self.sheet_name}!{column}{row}"
        body = {'values': [[value]]}

        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id, range=write_range,
            valueInputOption="RAW", body=body).execute()
    

    
    
