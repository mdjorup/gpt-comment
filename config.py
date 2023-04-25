config = {
    "spreadsheet" : {
        "spreadsheet_id": "1q5GTuEa5saL2XOiKhvmNZx7tez-Tf0ZlPSElEQ-ngi4",
        "sheet_name" : "Form Responses 1",
        "completed_column" : "B",
        "student_email_column" : "G",
        "parent_email_column" : "I",
        "document_link_column" : "D",
        "reported_gpa_column" : "L",
        "middle_school_column" : "K",
        "row_start" : 2,
        "sps_start_indicator": "SPS:",
        "pse_start_indicator": "PSE:",
    },
    "folder_id": "1jeEq39T2Devm1nhZghmaCAbGumBjZgWS", # this is the folder where the generated documents will be stored
    "generated_document_name": "set1",
    "limit" : 1,
    "contractions_data_path": "data/contractions.json",
    "service_account_file" : "gpt-comment-382218-c20de7caf068.json",
    "openai_api_key": "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",

}

# pricing per 1000 tokens, in dollars
pricing = {
    "gpt-3.5-turbo": 0.002 # this is the only model used but more could be added
}