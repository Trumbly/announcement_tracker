import os
from dotenv import load_dotenv
import googleapiclient.discovery
import googleapiclient.errors
from dataclasses import dataclass
from typing import List, Dict, Optional
import datetime
from sqlalchemy import create_engine, Integer, String, DateTime, ForeignKey, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, DeclarativeBase, Relationship

#Base = declarative_base()
class Base(DeclarativeBase):
    pass

# @dataclass
# class Thumbnails(Base):
#     url: str
#     width: int
#     height: int

@dataclass
class Snippet(Base):
    __tablename__ = "snippets"

    pk = Column(Integer, primary_key=True, autoincrement=True)

    publishedAt = Column(DateTime)
    channelId = Column(String)
    title = Column(String)
    description = Column(String)
    #thumbnails: Dict[str, Thumbnails]
    channelTitle = Column(String)
    liveBroadcastContent = Column(String)

    searchResourceId_fk = Column(Integer, ForeignKey("search_resource_id.pk"))
    searchResourceId = Relationship("SearchResourceId", back_populates="snippets")


    # def __init__(self, pubushedAt, channelId, title, description, channelTitle, liveBroadcastContent):
    #     self.publishedAt = pubushedAt
    #     self.channelId = channelId
    #     self.title = title
    #     self.description = description
    #     self.channelTitle = channelTitle
    #     self.liveBroadcastContent = liveBroadcastContent

    #searchRessourceId_fk:Mapped[int] = mapped_column(ForeignKey("search_ressource_id.pk"))
    #searchRessourceId: Mapped["SearchRessourceId"] = relationship(back_populates="snippets")

@dataclass
class SearchResourceId:
    __tablename__ = "search_resource_id"

    pk = Column(Integer, primary_key=True, autoincrement=True)

    kind = Column(String)
    videoId = Column(String)
    channelId = Column(String)
    playlistId = Column(String)
    snippets = Relationship("Snippet", back_populates="searchResourceId", uselist=True)  #List[Snippet]

    searchResource_fk = Column(Integer, ForeignKey("search_resource.pk"))
    searchResource = Relationship("SearchResource", back_populates="id")

@dataclass
class SearchResource:
    __tablename__ = "search_resource"

    pk = Column(Integer, primary_key=True, autoincrement=True)

    kind:str
    etag = Column(String)
    id = Relationship("SearchResourceId", back_populates="searchResourceId", uselist=True)  #List[SearchResourceId]

    

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

        # Create a PostgreSQL database connection
        POSTGRE_HOST = os.environ.get("POSTGRE_HOST")
        POSTGRE_PORT = os.environ.get("POSTGRE_PORT")
        POSTGRE_USER = os.environ.get("POSTGRE_USER")
        POSTGRE_PASSWORD = os.environ.get("POSTGRE_PASSWORD")
        engine = create_engine(f'postgresql+psycopg2://{POSTGRE_USER}:{POSTGRE_PASSWORD}@{POSTGRE_HOST}:{POSTGRE_PORT}/youtube', echo=True)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        #Execute youtube search 
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        youtube = googleapiclient.discovery.build(serviceName='youtube', version='v3', developerKey=GOOGLE_API_KEY)
        not_none_params = self.getSearchParameter()
        search_request = youtube.search().list(**not_none_params)
        request_response = search_request.execute()
        self.response = Response(**request_response)

        #session.add(self.response)
        session.commit()
        session.close()

        

search = Search(q="airport ambiance noise", type = "video", eventType = "completed")
search.execute()
print(search)