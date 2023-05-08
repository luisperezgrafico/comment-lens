from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# The following function fetch comments from YouTube:

def get_video_comments(api_key, video_id, max_results=100, page_token=None):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=max_results,
            pageToken=page_token,
            fields='items(snippet(topLevelComment(snippet(textDisplay)))),nextPageToken'
        )
        response = request.execute()
        comments = [item['snippet']['topLevelComment']['snippet']['textDisplay'] for item in response['items']]
        next_page_token = response.get('nextPageToken')
        return comments, next_page_token
    except HttpError as e:
        print(f"An error occurred: {e}")
        return [], None
