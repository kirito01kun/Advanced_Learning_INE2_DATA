from __future__ import print_function

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = "https://www.googleapis.com/auth/forms"
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

# Setup the OAuth2 credentials
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server()

form_service = build('forms', 'v1', credentials=creds, discoveryServiceUrl=DISCOVERY_DOC)

# Request body for creating a form
NEW_FORM = {
    "info": {
        "title": "Quickstart form",
    }
}

# Request body to add a multiple-choice question
NEW_QUESTION = {
    "requests": [{
        "createItem": {
            "item": {
                "title": "In what year did the United States land a mission on the moon?",
                "questionItem": {
                    "question": {
                        "required": True,
                        "choiceQuestion": {
                            "type": "RADIO",
                            "options": [
                                {"value": "1965"},
                                {"value": "1967"},
                                {"value": "1969"},
                                {"value": "1971"}
                            ],
                            "shuffle": True
                        }
                    }
                },
            },
            "location": {
                "index": 0
            }
        }
    }]
}

# Creates the initial form
result = form_service.forms().create(body=NEW_FORM).execute()

# Adds the question to the form
question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=NEW_QUESTION).execute()

# Prints the result to show the question has been added
get_result = form_service.forms().get(formId=result["formId"]).execute()
print(get_result)
