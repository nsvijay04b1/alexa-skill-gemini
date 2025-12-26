import os
import sys
import json
import logging

# Add current directory to path so we can import lambda_function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lambda_function import lambda_handler

# Mock Context Object
class Context:
    def __init__(self):
        self.aws_request_id = "mock-request-id"
        self.log_stream_name = "mock-log-stream"
        self.log_group_name = "mock-log-group"
        self.function_name = "mock-function"
        self.memory_limit_in_mb = 128
        self.function_version = "1"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:mock-function"
        self.client_context = None
        self.identity = None

def create_launch_request():
    return {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": "amzn1.echo-api.session.mock",
            "application": {
                "applicationId": "amzn1.ask.skill.mock"
            },
            "user": {
                "userId": "amzn1.ask.account.mock"
            }
        },
        "context": {
            "System": {
                "application": {
                    "applicationId": "amzn1.ask.skill.mock"
                },
                "user": {
                    "userId": "amzn1.ask.account.mock"
                },
                "device": {
                    "supportedInterfaces": {}
                }
            }
        },
        "request": {
            "type": "LaunchRequest",
            "requestId": "amzn1.echo-api.request.mock",
            "timestamp": "2023-01-01T00:00:00Z",
            "locale": "en-US"
        }
    }

def create_chat_intent(query, session_attributes=None):
    if session_attributes is None:
        session_attributes = {}
        
    return {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": "amzn1.echo-api.session.mock",
            "application": {
                "applicationId": "amzn1.ask.skill.mock"
            },
            "user": {
                "userId": "amzn1.ask.account.mock"
            },
            "attributes": session_attributes
        },
        "context": {
            "System": {
                "application": {
                    "applicationId": "amzn1.ask.skill.mock"
                },
                "user": {
                    "userId": "amzn1.ask.account.mock"
                },
                "device": {
                    "supportedInterfaces": {}
                }
            }
        },
        "request": {
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.mock",
            "timestamp": "2023-01-01T00:00:00Z",
            "locale": "en-US",
            "intent": {
                "name": "ChatIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "query": {
                        "name": "query",
                        "value": query,
                        "confirmationStatus": "NONE"
                    }
                }
            }
        }
    }

def run_test():
    print("--- Starting Simulation ---")
    
    # Check for API KEY
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY not found in environment. API calls will fail.")
    else:
        print("GOOGLE_API_KEY found.")

    context = Context()

    # 1. Test Launch Request
    print("\n[1] Testing LaunchRequest...")
    launch_event = create_launch_request()
    response = lambda_handler(launch_event, context)
    print("Response Output Speech:", response['response']['outputSpeech']['ssml'])
    
    # Extract session attributes for next turn
    session_attributes = response.get('sessionAttributes', {})
    
    # 2. Test Chat Intent
    print("\n[2] Testing ChatIntent (What is the capital of France?)...")
    chat_event = create_chat_intent("What is the capital of France?", session_attributes)
    response = lambda_handler(chat_event, context)
    print("Response Output Speech:", response['response']['outputSpeech']['ssml'])
    
    # Update attributes
    session_attributes = response.get('sessionAttributes', {})
    
    # 3. Test Follow-up (Context awareness check)
    print("\n[3] Testing ChatIntent Follow-up (What is its population?)...")
    chat_event_2 = create_chat_intent("What is its population?", session_attributes)
    response = lambda_handler(chat_event_2, context)
    print("Response Output Speech:", response['response']['outputSpeech']['ssml'])
    
    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_test()
