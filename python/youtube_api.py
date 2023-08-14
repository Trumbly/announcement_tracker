import os
from dotenv import load_dotenv
import googleapiclient.discovery
import googleapiclient.errors
from dataclasses import dataclass
from typing import List, Dict
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


@dataclass
class Thumbnails:
    url: str
    width: int
    height: int

@dataclass
class Snippet:
    publishedAt: datetime
    channelId: str
    title: str
    description: str
    #thumbnails: Dict[str, Thumbnails]
    channelTitle: str
    liveBroadcastContent: str
    

@dataclass
class searchRessourceId:
    kind: str
    videoId: str
    channelId: str
    playlistId: str
    snippet: List[Snippet]


@dataclass
class SearchResource:
    kind: str
    etag: str
    id: List[searchRessourceId]

    

@dataclass
class PageInfo:
    totalResults: int
    resultsPerPage: int


@dataclass
class Response:
    kind: str
    etag: str
    nextPageToken: str
    #prevPageToken: str #TODO prevPageToken seems to be missing in API response
    regionCode: str
    pageInfo: List[PageInfo]
    items: List[SearchResource]


@dataclass
class Search:

    #https://developers.google.com/youtube/v3/docs/search/list?hl=de
    #requried
    part: str = "snippet"
    #filter
    forContentOwner: bool = None
    forDeveloper: bool = None
    forMine: bool = None
    relatedToVideoId: str = None
    #optional
    channelId: str = None
    channelType: str = None
    eventType: str = None
    location: str = None
    locationRadius: str = None
    maxResults: int = None
    onBehalfOfContentOwner: str = None
    order: str = None
    pageToken: str = None
    publishedAfter: str = None
    publishedBefore: str = None
    q: str = None
    regionCode: str = None
    relevanceLanguage: str = None
    safeSearch: str = None
    topicId: str = None
    type: str = None
    videoCaption: str = None
    videoCategoryId: str = None
    videoDefinition: str = None
    videoDimension: str = None
    videoDuration: str = None
    videoEmbeddable: str = None
    videoLicense: str = None
    videoSyndicated: str = None
    videoType: str = None

    response: Response = None


    def getSearchParameter(self):
        self_attrs = vars(self)
        not_none_params = {k:v for k, v in self_attrs.items() if v is not None}
        #remove params from not_none_params
        if 'id' in not_none_params:
            del not_none_params['id']
        if 'repsonse' in not_none_params:
            del not_none_params['response']
        return not_none_params

    
    def execute(self):
        load_dotenv() #load environment variables from .env file

        #Execute youtube search 
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        youtube = googleapiclient.discovery.build(serviceName='youtube', version='v3', developerKey=GOOGLE_API_KEY)
        not_none_params = self.getSearchParameter()
        search_request = youtube.search().list(**not_none_params)
        request_response = search_request.execute()
        self.response = Response(**request_response)

        

search = Search(q="airport ambiance noise", type = "video", eventType = "completed")
search.getSearchParameter()
search.execute()
print(search)