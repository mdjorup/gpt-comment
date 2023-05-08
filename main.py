### THIS IS A COMMENT

import asyncio
import sys

from config import config
from services.sheets_service import SheetsService
from student_entry import StudentEntry
from utils import float_to_dollar


async def main():
    ### PART 1: GET DATA FROM SHEET
    limit: int = config["limit"]
    completed_column: str = config["spreadsheet"]["completed_column"]
    student_email_column: str = config["spreadsheet"]["student_email_column"]
    parent_email_column: str = config["spreadsheet"]["parent_email_column"]
    reported_gpt_column: str = config["spreadsheet"]["reported_gpa_column"]
    middle_school_column: str = config["spreadsheet"]["middle_school_column"]

    student_email_index = ord(student_email_column) - 65
    parent_email_index = ord(parent_email_column) - 65
    complted_index = ord(completed_column) - 65
    reported_gpa_index = ord(reported_gpt_column) - 65
    middle_school_index = ord(middle_school_column) - 65

    ss = SheetsService()

    df = ss.get_rows()

    student_entries: list[StudentEntry] = []

    i = config["spreadsheet"]["row_start"]
    n = 0

    for _, row in df.iterrows():
        if n >= limit:
            break

        assert student_email_index >= 0, "Invalid student email column"
        assert complted_index >= 0, "Invalid completed column"

        student_email = row[student_email_index]

        if row[complted_index] != "TRUE" and student_email != None:
            gpa_str = str(row[reported_gpa_index])
            entry = StudentEntry(
                dict(row),
                i,
                row[student_email_index],
                row[parent_email_index],
                gpa_str,
                row[middle_school_index],
            )
            if len(entry.sps_essays) != 0 or len(entry.pse_essays) != 0:
                student_entries.append(entry)
                n += 1
        i += 1

    if n == 0:
        print("No new entries to process")
        sys.exit(0)

    total_cost = 0
    for entry in student_entries:
        cost = await entry.process()
        total_cost += cost

    print("Successfully processed " + str(n) + f" submission{'s' if n > 1 else ''}")
    print("Total cost: " + float_to_dollar(total_cost))


if __name__ == "__main__":
    asyncio.run(main())
