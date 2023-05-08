import os
from dotenv import load_dotenv
import requests
from typing import List, Tuple

load_dotenv()

from requests.exceptions import RequestException

def analyze_comments(api_key: str, comments: List[str], model: str = "gpt-3.5-turbo", chunk_index: int = 0, total_chunks: int = 1) -> str:
    message_content = f"Act as a marketing specialist, analyze the following comments (chunk {chunk_index + 1} of {total_chunks}) then elaborate the insights into categories with bullet points, you can categorize e.g by sentiment, feedback, expectation, or whatever works better with the current comments. :\n\n" + "\n".join(comments)

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "As the chief comment analyst, you are tasked with analyzing the comments on our social media channel to identify patterns and provide insights that can inform our content strategy. Your job is to analyze the following comments and provide insights on the topics, sentiments, and audience demographics that are most relevant to our channel."
            },
            {
                "role": "user",
                "content": message_content
            }
        ],
        "max_tokens": 130,
        "temperature": 0.8
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
    except RequestException as e:
        print(f"RequestException: {e}")
        return f"Error: Failed to analyze comments. RequestException: {e}"

    if response.status_code == 200:
        json_response = response.json()
        print(f"API response: {json_response}")
        insights = json_response['choices'][0]['message']['content'].strip().split('\n')
        return insights
    else:
        print(f"Error details: {response.status_code}, {response.text}")
        return f"Error: Failed to analyze comments. StatusCode: {response.status_code}, ResponseText: {response.text}"





def summarize_insights(insights: List[str], api_key: str, model: str = "gpt-3.5-turbo") -> str:

    message_content = "The chunks of insights bellow comes from the same video, just different batches of comments, please merge the insights into a single coherent list:\n" + "\n".join(insights)

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "As the chief comment analyst, you are tasked with analyzing the comments on our social media channel to identify patterns and provide insights that can inform our content strategy. Your job is to summarize a list of insights gathered from the comment section of our video into a single coherent list of insights with titles."
            },
            {
                "role": "user",
                "content": message_content
            }
        ],
        "max_tokens": 400,
        "temperature": 0.8
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)

    if response.status_code == 200:
        json_response = response.json()
        merged_insights = json_response['choices'][0]['message']['content'].strip().split('\n')
        return "<br>".join(merged_insights)  # Replace the newline character with the HTML line break tag

    else:
        print(f"Error details: {response.status_code}, {response.text}")
        return "Error: Failed to merge insights."

