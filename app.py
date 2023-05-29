import speech_recognition as sr
from pydub import AudioSegment
import openai
from flask import Flask, request, jsonify, render_template, redirect
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# Set your OpenAI API key
openai.api_key = "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"

app = Flask(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.external_request"
]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

# Set up the OAuth2 credentials
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/transcribe', methods=['GET', 'POST'])
def transcribe():
    try:
        # Retrieve the uploaded audio file
        audio_file = request.files['audio']

        # Create a recognizer instance
        recognizer = sr.Recognizer()

        # Load the audio data
        audio_data = AudioSegment.from_file(audio_file, format='mp3').export(format='wav')

        # Perform speech recognition
        with sr.AudioFile(audio_data) as source:
            audio = recognizer.record(source)

        # Convert audio to text
        #questiontxt = recognizer.recognize_google(audio)
        questiontxt = "what is the capital of Morocco?"
        prompt = f"""
                Generate a quiz question based on the following prompt:

                Prompt: {questiontxt}

                Write a multiple-choice question with four answer choices. The correct answer should be indicated by a star (*) at the end of answer.

                Example:
                * What is the capital of France?
                A) London
                B) Paris
                C) Berlin
                D) Rome
                """
        # Prepare the prompt for ChatGPT
        payload = {
            "prompt": prompt,
            "max_tokens": 1000,  # Set the desired maximum number of tokens in the response
            "model": "text-davinci-003"  # Use the Ada model
        }

        # Make a request to the ChatGPT API using the Ada model
        response = openai.Completion.create(**payload)

        # Extract the generated reply
        if response['choices']:
            reply = response['choices'][0]['text']
            # Split the reply into lines
            lines = reply.split("\n")
            lines = list(filter(None, lines))

            # Extract the question
            question_line = lines[0].strip()
            if question_line.startswith("Question:") or question_line.startswith("Q:"):
                question = question_line.replace("Question:", "").replace("Q:", "").strip()
            else:
                # Combine the separate lines into a single question
                question = " ".join(
                    line.strip() for line in lines if not line.startswith("A)") and not line.startswith("Q:"))

            # Extract the answer choices
            choices = [line.strip() for line in lines[1:]]

            # Extract the correct answer
            correct_answer = None
            for choice in choices:
                if choice.endswith("*"):
                    correct_answer = choice.replace("*", "").strip()
                    break

            print(choices)
            print(question)
            # Set up the Google Forms API
            form_service = build('forms', 'v1', credentials=creds, discoveryServiceUrl=DISCOVERY_DOC)

            # Create the initial form
            new_form = {
                "info": {
                    "title": "Generated Quiz"
                }
            }
            result = form_service.forms().create(body=new_form).execute()

            # Add the question to the form
            new_question = {
                "requests": [
                    {
                        "createItem": {
                            "item": {
                                "title": question,
                                "questionItem": {
                                    "question": {
                                        "required": True,
                                        "choiceQuestion": {
                                            "type": "RADIO",
                                            "options": [
                                                {
                                                    "value": choices[0]
                                                },
                                                {
                                                    "value": choices[1]
                                                },
                                                {
                                                    "value": choices[2]
                                                },
                                                {
                                                    "value": choices[3]
                                                }
                                            ],
                                            "shuffle": False
                                        }
                                    }
                                }
                            },
                            "location": {
                                "index": 0
                            }
                        }
                    }
                ]
            }

            question_settings = form_service.forms().batchUpdate(
                formId=result["formId"], body=new_question).execute()

            # Get the URL of the created form
            form_url = result.get("formUrl", "")

        else:
            reply = "No reply generated."

        return redirect(form_url)

        #print(lines)
        #print("Question:", question)
        #print("Answer Choices:", choices)
        #print("Correct Answer:", correct_answer)

        #return reply

    except Exception as e:
        print(str(e))
        return str(e), 400


if __name__ == '__main__':
    app.run()
