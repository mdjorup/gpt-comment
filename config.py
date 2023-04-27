from dotenv import load_dotenv

load_dotenv()
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
    "gpt_model_id": "gpt-3.5-turbo", # Do not change until you have access to GPT-4
    "folder_id": "1jeEq39T2Devm1nhZghmaCAbGumBjZgWS", # this is the folder where the generated documents will be stored
    "generated_document_name": "Self-Paced Feedback Set #1",
    "limit" : 1,
    "contractions_data_path": "data/contractions.json"
}

# pricing per 1000 tokens, in dollars
pricing = {
    "gpt-3.5-turbo": {
        "prompt_tokens": 0.002,
        "completion_tokens": 0.002,    
    },
    "gpt-4": {
        "prompt_tokens": 0.03,
        "completion_tokens": 0.06,   
    } 
}