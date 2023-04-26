# GPTComment: AI-Powered Essay Review and Feedback Tool

GPTComment is an intelligent, automated essay review and feedback tool that streamlines the editing process. Leveraging advanced natural language processing techniques, GPTComment reads essays from a spreadsheet and generates comprehensive, well-structured, and insightful comments on Google Docs. These comments include suggested edits, improvements, and general feedback aimed at enhancing the quality and clarity of the essays. GPTComment is powered by OpenAI's GPT-3 API, which is trained on a massive dataset of essays and other writing samples. This allows GPTComment to provide context-aware feedback that is tailored to the specific essay.

## Features
 - Seamless integration with Google Sheets and Google Docs
 - AI-powered analysis for in-depth essay evaluation using OpenAI API
 - Context-aware recommendations for edits and improvements
 - Customizable commenting options for personalized feedback
 - Streamlined workflow to expedite the editing process

## System Requirements
 - Python 3.11

## Configuration
 - Fill in the necessary fields in config.py to set up API access keys and credentials for Google Sheets, Google Docs, and OpenAI.
- Define the interactions with the spreadsheet by specifying the sheet ID, range, and other necessary parameters in config.py.
- Specify how the generated Google Docs will be named and organized in config.py.

## Project Structure
 - main.py - The main script that runs the application
 - student_entry.py - Contains a class representing a set of essays from a single student
 - essay.py - A class representing an individual essay written by a student
 - comments.py - Contains various classes for generating different types of comments
 - services/ - A folder containing classes representing the services used in the application, including OpenAI, Google Sheets, and Google Drive

## License
This project is open source and available under the MIT License.

Note: This project is not affiliated with, sponsored by, or endorsed by Google or OpenAI. It is an independent project that utilizes their APIs to provide an automated essay review and feedback tool.