import os
import openai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify


load_dotenv()  
openai.api_key = os.getenv('OPENAI_API_KEY') 

app = Flask(__name__)

def generate_gpt_response(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,
            n=1,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except openai.error.InvalidRequestError as e:
        print(f"InvalidRequestError: {e}")
        return f"Error: Failed to generate response. InvalidRequestError: {e}"


@app.route('/')
def index():
    return render_template('smart-gpt.html')

@app.route('/process_input', methods=['POST'])
def process_input():
    user_message = request.json['input']
    print(f"User message: {user_message}")

    prefixed_message = f"Act as an expert software engineer and ask this question: {user_message} Answer: Let's work this out in a step by step way to be sure we have the right answer."
    print(f"Prefixed message: {prefixed_message}")

    answer_options = []
    for i in range(3):
        answer_option = generate_gpt_response([
            {"role": "user", "content": prefixed_message},
        ])
        print(f"Answer option {i + 1}: {answer_option}")
        answer_options.append(f"Answer Option {i + 1}: {answer_option}")

    researcher_prompt = f"{user_message}\n\n" + "\n".join(answer_options)
    researcher_prompt += '\n\nYou are an expert software researcher tasked with investigating the three answer options provided. List the flaws and faulty logic of each answer option. Let\'s think step by step:'

    researcher_response = generate_gpt_response([
        {"role": "user", "content": researcher_prompt},
    ])
    print(f"Researcher response: {researcher_response}")

    resolver_prompt = f"{researcher_response}\n\nYou are an expert software engineer and resolver tasked with 1) finding which of the answer options the researcher thought was best, 2) improving that answer, and 3) Printing the improved answer in full. Let's work this out in a step by step way to be sure we have the right answer:"
    resolver_response = generate_gpt_response([
        {"role": "user", "content": resolver_prompt},
    ])
    print(f"Resolver response: {resolver_response}")

    return jsonify({'output': resolver_response})


if __name__ == '__main__':
    app.run(debug=True)
