# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import requests
import json
import os
from dotenv import load_dotenv
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# API endpoint URL
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
# API endpoint URL
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}".format(GEMINI_MODEL, GOOGLE_API_KEY)


def call_gemini_api(history):
    """
    Calls the Gemini API with the provided chat history.
    
    :param history: List of dicts with role and parts.
    :return: Tuple (text_response, error_message).
    """
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "contents": history
    }
    
    try:
        response = requests.post(GEMINI_URL, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        
        response_data = response.json()
        text = (response_data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text"))
        return text, None
    except requests.exceptions.RequestException as e:
        logger.error(f"API Request failed: {e}")
        error_msg = str(e).replace(GOOGLE_API_KEY, "API_KEY_HIDDEN")
        return None, error_msg
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing API response: {e}")
        return None, f"Parsing Error: {str(e)}"


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        # Initialize session history
        session_attr = handler_input.attributes_manager.session_attributes
        if "history" not in session_attr:
            session_attr["history"] = []

        # Silent System Prompt: Add to history but do not call API.
        # This ensures the 300-word limit is respected in future turns without paying for a generation now.
        max_words = os.getenv('MAX_RESPONSE_WORDS', '300')
        system_instruction = f"Hello! Respond in English clearly and keep your response under {max_words} words. OK?"
        
        session_attr["history"].append({"role": "user", "parts": [{"text": system_instruction}]})
        session_attr["history"].append({"role": "model", "parts": [{"text": "Understood. I will keep responses concise."}]})
        
        speak_output = "I am google gemini, How can I help you?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class ChatIntentHandler(AbstractRequestHandler):
    """Handler for Chat Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ChatIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        query = handler_input.request_envelope.request.intent.slots["query"].value
        
        session_attr = handler_input.attributes_manager.session_attributes
        if "history" not in session_attr:
            session_attr["history"] = []
            
        # Append user query to history
        user_turn = {
                "role": "user",
                "parts": [{"text": query}]
        }
        session_attr["history"].append(user_turn)
        
        # Call API with full history
        text, error = call_gemini_api(session_attr["history"])
        
        if text:
            speak_output = text
            # Append model response to history
            model_turn = {
                "role": "model",
                "parts": [{"text": text}]
            }
            session_attr["history"].append(model_turn)
        else:
            speak_output = f"I did not receive a response. Debug Error: {error}"
            # Remove the last user turn since we failed to process it? 
            # Or keep it? Usually better to remove if we want to retry clean, 
            # but for simplicity let's leave it or remove it. Removing is safer to avoid confusion.
            session_attr["history"].pop() 

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Any other questions?")
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ChatIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
