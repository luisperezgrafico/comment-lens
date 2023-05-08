import os
from typing import List
from flask import Flask, request, jsonify
from openai_call import analyze_comments
from youtube import get_video_comments
from openai_call import summarize_insights
from tiktoken import encoding_for_model
from flask import render_template

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)
app.progress_status = "idle"
app.total_chunks = 0
app.current_chunk = 0


@app.route('/')
def index():
    return render_template('index.html')

# Handle YouTube comment fetching

@app.route('/fetch_youtube_comments', methods=['POST'])
def fetch_youtube_comments():
    data = request.get_json()
    video_url = data.get('video_url')
    max_results = data.get('max_results', 100)
    page_token = data.get('page_token', None)

    # Extract video ID from the URL
    video_id = video_url.split("watch?v=")[-1]

    all_comments = []
    while len(all_comments) < max_results:
        comments, next_page_token = get_video_comments(os.getenv("YOUTUBE_API_KEY"), video_id, max_results - len(all_comments), page_token)
        
        all_comments.extend(comments)

        # If there are no more comments to fetch, break the loop
        if next_page_token is None:
            break
        else:
            page_token = next_page_token

    return jsonify({"comments": all_comments, "next_page_token": next_page_token})



# Add the route definition for analyzing comments
@app.route('/analyze_comments', methods=['POST'])
def analyze_comments_route():
    # Parse the request data
    data = request.get_json()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    comments = data.get('comments')
    model = data.get('model', 'gpt-3.5-turbo')

    token_limit = 3500 if model == 'gpt-3.5-turbo' else 8000

    # Split the comments into chunks based on the model's token limit
    comment_chunks = split_comments_by_token_limit(comments, token_limit)

    # Update the progress status and total chunks
    app.progress_status = "analyzing"
    app.total_chunks = len(comment_chunks)

    # Call the analyze_comments function for each chunk and collect the insights
    insights = []
    for i, chunk in enumerate(comment_chunks):
        app.current_chunk = i + 1  # Update the current chunk
        chunk_insights = analyze_comments(openai_api_key, chunk, model=model, chunk_index=i, total_chunks=len(comment_chunks))
        insights.extend(chunk_insights)

        # Additional logging
        print(f"Chunk {i+1}/{len(comment_chunks)}:")
        print(f"Number of tokens in chunk: {sum([len(encoding_for_model(model).encode(comment)) for comment in chunk])}")
        print(f"Insights for chunk {i+1}:")
        for insight in chunk_insights:
            print(insight)
        print("\n")

    # Update the progress status to summarizing
    app.progress_status = "summarizing"

    if len(comment_chunks) > 1:
        summarized_insights = summarize_insights(insights, openai_api_key, model=model)
    else:
        summarized_insights = insights

    # Reset the progress status to idle
    app.progress_status = "idle"

    return jsonify({"insights": summarized_insights})





# Uses form data and calls the /fetch_youtube_comments and /analyze_comments routes internally.

from flask import render_template

@app.route('/analyze_comments_form', methods=['POST'])
def analyze_comments_form():
    # Use form data instead of JSON data
    video_url = request.form.get('video_url')
    max_results = int(request.form.get('max_results', 100))
    model = request.form.get('model', 'gpt-3.5-turbo')

    # Fetch YouTube comments
    comments_data = {
        'video_url': video_url,
        'max_results': max_results,
    }
    with app.test_request_context(json=comments_data, method='POST'):
        comments_response = fetch_youtube_comments().get_json()
    comments = comments_response.get('comments')

    # Call the analyze_comments_route
    analyze_data = {
        'comments': comments,
        'model': model,
    }
    with app.test_request_context(json=analyze_data, method='POST'):
        insights_response = analyze_comments_route().get_json()
    insights = insights_response.get('insights')

    # Return the summarized_insights as an HTML response
    return render_template('insights.html', insights=insights)




# function to split the comments based on a given token limit:

def split_comments_by_token_limit(comments, token_limit):
    tokenizer = encoding_for_model('gpt-3.5-turbo')
    current_chunk = []
    current_chunk_token_count = 0
    chunks = []

    for comment in comments:
        try:
            comment_token_count = len(tokenizer.encode(comment))
        except Exception:
            continue

        if comment_token_count >= token_limit:
            comment = tokenizer.decode(tokenizer.encode(comment)[:token_limit])
            comment_token_count = token_limit - 1

        if current_chunk_token_count + comment_token_count + 1 <= token_limit:
            current_chunk.append(comment)
            current_chunk_token_count += comment_token_count + 1
        else:
            chunks.append(current_chunk)
            current_chunk = [comment]
            current_chunk_token_count = comment_token_count + 1

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# Handles process updates

from flask import Blueprint
progress = Blueprint('progress', __name__)

@progress.route('/progress')
def progress_updates():
    return jsonify({"status": app.progress_status, "total_chunks": app.total_chunks, "current_chunk": app.current_chunk})

app.register_blueprint(progress, url_prefix='/api')


if __name__ == '__main__':
    app.run(debug=True)
