from pathlib import Path
import tempfile
from googleapiclient.discovery import build
import os
import subprocess
import time
API_KEY="AIzaSyD6imOVEK2r377fbK7BTjFNCPwzv3dLQFg"

  
class YoutubeFeeder:
    def __init__(self, api_key: str, query: str, max_results:int = 10, filters:dict| None = None ):
        self.api_key = api_key
        self.query = query
        self.max_results = max_results
        self.filters = filters or {}
        
    def feed(self):
        youtube = build("youtube","v3", developerKey = self.api_key)
        request = youtube.search().list(
            q = self.query,
            part = "snippet",
            type ="video",
            maxResults = self.max_results,
            **self.filters
        )
        return request.execute()

class YoutubeParser:
    def parse(self, response: dict):
        videos = []
        for item in response.get("items", []):
            try:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append({
                    "title": title,
                    "video_id": video_id,
                    "url": url
                })
            except KeyError:
                continue
        return videos

class YoutubeDownloader:
    def __init__(self, output_dir: str, download_video: bool = True):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.download_video = download_video
    
    def download(self, videos: list):
        for video in videos:
            print(f"Downloading URL: {video['url']}") 
            print(f"📥 Downloading: {video['title']}")
            if self.download_video:
                try:
                    timestamp = time.strftime("%d_%m_%y_%H")
                    sanitized_title = "".join(c for c in video['title'] if c.isalnum() or c in (' ', '_')).rstrip()
                    output_template = f'{self.output_dir}/{timestamp}_{sanitized_title}.%(ext)s'
                    subprocess.run([
                        'yt-dlp',
                        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        '-o', output_template,
                        video['url']
                    ], check=True)
                    print(f"✅ Done: {video['title']}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to download {video['title']}: {e}")
                except Exception as e:
                    print(f"❌ An unexpected error occurred while downloading {video['title']}: {e}")

class YoutubevideoCrawler:
    def __init__(self, api_key = API_KEY, storage:dict|None = None, download_video: bool = True):
        if not api_key:
            raise ValueError("YouTube API key is not set. Please set the YOUTUBE_API_KEY environment variable.")
        self.api_key = api_key 
        self.root_dir = Path(storage.get("root_dir") if storage else tempfile.mkdtemp(prefix ="ytcrawl_"))
        self.root_dir.mkdir(parents= True, exist_ok= True)
        self.download_video = download_video
    
    def crawl(self, keyword: str, max_num: int = 5, filters: dict|None = None):
        feeder = YoutubeFeeder(api_key= self.api_key,query = keyword, max_results= max_num, filters = filters)
        parser = YoutubeParser()
        downloader = YoutubeDownloader(output_dir = str(self.root_dir), download_video= self.download_video)
        
        response = feeder.feed()
        video_data = parser.parse(response)
        downloader.download(video_data)
        
        