import os
from dotenv import load_dotenv
import googleapiclient.discovery
import googleapiclient.errors
from dataclasses import dataclass
from sqlalchemy import create_engine, Integer, String, DateTime, ForeignKey, Column, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Relationship

load_dotenv() #load environment variables from .env file

# Create a PostgreSQL database connection
POSTGRE_HOST = os.environ.get("POSTGRE_HOST")
POSTGRE_PORT = os.environ.get("POSTGRE_PORT")
POSTGRE_USER = os.environ.get("POSTGRE_USER")
POSTGRE_PASSWORD = os.environ.get("POSTGRE_PASSWORD")
engine = create_engine(f'postgresql+psycopg2://{POSTGRE_USER}:{POSTGRE_PASSWORD}@{POSTGRE_HOST}:{POSTGRE_PORT}/youtube', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


# @dataclass
# class Thumbnails(Base):
#     url: str
#     width: int
#     height: int

@dataclass
class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    publishedAt = Column(DateTime)
    publishTime = Column(DateTime)
    channelId = Column(String)
    title = Column(String)
    description = Column(String)
    #thumbnails: Dict[str, Thumbnails]
    channelTitle = Column(String)
    liveBroadcastContent = Column(String)
    searchResource_id = Column(Integer, ForeignKey("search_resources.id"))
    searchResource = Relationship("SearchResource", back_populates="snippet")


    def __init__(self, publishedAt, channelId, title, description, channelTitle, liveBroadcastContent, publishTime, thumbnails):
        self.publishedAt = publishedAt
        self.channelId = channelId
        self.title = title
        self.description = description
        self.channelTitle = channelTitle
        self.liveBroadcastContent = liveBroadcastContent
        self.publishTime = publishTime

    
@dataclass
class SearchResourceId(Base):
    __tablename__ = "search_resource_id"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String)
    videoId = Column(String, nullable=True)
    channelId = Column(String, nullable=True)
    playlistId = Column(String, nullable=True)

    searchResource_id = Column(Integer, ForeignKey("search_resources.id"))
    searchResource = Relationship("SearchResource", back_populates="searchResourceId")

    def __init__(self, kind, videoId, channelId=None, playlistId=None):
        self.kind=kind
        self.videoId = videoId
        self.channelId = channelId
        self.playlistId = playlistId


@dataclass
class SearchResource(Base):
    __tablename__ = "search_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String)
    etag = Column(String)
    searchResourceId = Relationship("SearchResourceId", back_populates="searchResource", uselist=False)
    snippet = Relationship("Snippet", back_populates="searchResource", uselist=False) 
    response_id = Column(Integer, ForeignKey("responses.id"))
    response = Relationship("Response", back_populates="searchResources", )
    
    def __repr__(self) -> str:
        return(f"SearchResource(kind={self.kind}, etag={self.etag})")

    def __init__(self, kind, etag, id, snippet):
        self.kind = kind
        self.etag = etag
        self.snippet = Snippet(**snippet)
        self.searchResourceId= SearchResourceId(**id)


@dataclass
class PageInfo(Base):
    __tablename__ = "page_infos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    totalResults = Column(Integer)
    resultsPerPage = Column(Integer)
    response_id = Column(Integer, ForeignKey("responses.id"))
    response = Relationship("Response", back_populates="pageInfo")

    def __init__(self, totalResults, resultsPerPage):
        self.totalResults = totalResults
        self.resultsPerPage = resultsPerPage


@dataclass
class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String)
    etag = Column(String)
    nextPageToken = Column(String)
    prevPageToken = Column(String, nullable=True)
    regionCode = Column(String)
    pageInfo = Relationship("PageInfo", back_populates="response", uselist=False)
    searchResources= Relationship("SearchResource", back_populates="response")
    search_id = Column(Integer, ForeignKey("searches.id"))
    search = Relationship("Search", back_populates="response")

    def __init__(self, kind, etag, nextPageToken, regionCode, pageInfo, items, prevPageToken=None):
        self.kind = kind
        self.etag = etag
        self.nextPageToken = nextPageToken
        self.prevPageToken = prevPageToken
        self.regionCode = regionCode
        self.pageInfo = PageInfo(**pageInfo)
        self.searchResources = [SearchResource(**item) for item in items]


@dataclass
class Search(Base):
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    part = Column(String)
    forContentOwner = Column(Boolean, nullable=True)
    forDeveloper = Column(Boolean, nullable=True)
    forMine = Column(Boolean, nullable=True)
    relatedToVideoId = Column(String, nullable=True)
    channelId = Column(String, nullable=True)
    channelType = Column(String, nullable=True)
    eventType = Column(String, nullable=True)
    location = Column(String, nullable=True)
    locationRadius = Column(String, nullable=True)
    maxResults = Column(Integer, nullable=True)
    onBehalfOfContentOwner = Column(String, nullable=True)
    order = Column(String, nullable=True)
    pageToken = Column(String, nullable=True)
    publishedAfter = Column(String, nullable=True)
    publishedBefore = Column(String, nullable=True)
    q = Column(String, nullable=True)
    regionCode = Column(String, nullable=True)
    relevanceLanguage = Column(String, nullable=True)
    safeSearch = Column(String, nullable=True)
    topicId = Column(String, nullable=True)
    type = Column(String, nullable=True)
    videoCaption = Column(String, nullable=True)
    videoCategoryId = Column(String, nullable=True)
    videoDefinition = Column(String, nullable=True)
    videoDimension = Column(String, nullable=True)
    videoDuration = Column(String, nullable=True)
    videoEmbeddable = Column(String, nullable=True)
    videoLicense = Column(String, nullable=True)
    videoSyndicated = Column(String, nullable=True)
    videoType = Column(String, nullable=True)
    response = Relationship("Response", back_populates="search", uselist=False)

    def __init__(self, part, forContentOwner=None, forDeveloper=None, forMine=None, relatedToVideoId=None, channelId=None, channelType=None, eventType=None, 
                location=None, locationRadius=None, maxResults=None, onBehalfOfContentOwner= None, order=None, pageToken=None, publishedAfter=None, publishedBefore=None, 
                q=None, regionCode=None, relevanceLanguage=None, safeSearch=None, topicId=None, type=None, videoCaption=None, videoCategoryId=None, videoDefinition=None, 
                videoDimension=None, videoDuration=None, videoEmbeddable=None, videoLicense=None, videoSyndicated=None, videoType=None, response=None):
        self.part=part
        self.forContentOwner = forContentOwner
        self.forDeveloper = forDeveloper
        self.forMine = forMine
        self.relatedToVideoId = relatedToVideoId
        self.channelId = channelId
        self.channelType = channelType
        self.eventType = eventType
        self.location = location
        self.locationRadius = locationRadius
        self.maxResults = maxResults
        self.onBehalfOfContentOwner = onBehalfOfContentOwner
        self.order = order
        self.pageToken = pageToken
        self.publishedAfter = publishedAfter
        self.publishedBefore = publishedBefore
        self.q = q
        self.regionCode = regionCode
        self.relevanceLanguage = relevanceLanguage
        self.safeSearch = safeSearch
        self.topicId = topicId
        self.type = type
        self.videoCaption = videoCaption
        self.videoCategoryId = videoCategoryId
        self.videoDefinition = videoDefinition
        self.videoDimension = videoDimension
        self.videoDuration = videoDuration
        self.videoEmbeddable = videoEmbeddable
        self.videoLicense = videoLicense
        self.videoSyndicated = videoSyndicated
        self.videoType = videoType
        self.response = response

    def getSearchParameter(self):
        self_attrs = vars(self)
        not_none_params = {k:v for k, v in self_attrs.items() if v is not None}
        #remove params from not_none_params
        if 'id' in not_none_params:
            del not_none_params['id']
        if 'repsonse' in not_none_params:
            del not_none_params['response']
        if '_sa_instance_state' in not_none_params:
            del not_none_params['_sa_instance_state']
        return not_none_params

    
    def execute(self):
        #Execute youtube search 
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        youtube = googleapiclient.discovery.build(serviceName='youtube', version='v3', developerKey=GOOGLE_API_KEY)
        not_none_params = self.getSearchParameter()
        search_request = youtube.search().list(**not_none_params)
        request_response = search_request.execute()
        self.response = Response(**request_response)


Base.metadata.create_all(bind=engine)
#TODO steer search
search = Search(part="snippet", q="airport ambiance noise", type = "video", eventType = "completed")
session.add(search)
search.execute()

session.commit()
session.close()