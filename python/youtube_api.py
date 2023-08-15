import os
from dotenv import load_dotenv
import googleapiclient.discovery
import googleapiclient.errors
from dataclasses import dataclass
from typing import List, Dict, Optional
import datetime
from sqlalchemy import create_engine, Integer, String, DateTime, ForeignKey, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, DeclarativeBase, Relationship, relationship

#Base = declarative_base()
class Base(DeclarativeBase):
    pass

# @dataclass
# class Thumbnails(Base):
#     url: str
#     width: int
#     height: int

# @dataclass
# class Snippet(Base):
#     __tablename__ = "snippets"

#     pk = Column(Integer, primary_key=True, autoincrement=True)

#     publishedAt = Column(DateTime)
#     channelId = Column(String)
#     title = Column(String)
#     description = Column(String)
#     #thumbnails: Dict[str, Thumbnails]
#     channelTitle = Column(String)
#     liveBroadcastContent = Column(String)

#     searchResourceId_fk: Mapped[int] = mapped_column(ForeignKey("search_resource_id.pk")) #Column(Integer, ForeignKey("search_resource_id.pk"))
    # searchResourceId: Mapped["SearchResourceId"] = relationship(back_populates="snippets") #Relationship("SearchResourceId", back_populates="snippets")


    # def __init__(self, pubushedAt, channelId, title, description, channelTitle, liveBroadcastContent):
    #     self.publishedAt = pubushedAt
    #     self.channelId = channelId
    #     self.title = title
    #     self.description = description
    #     self.channelTitle = channelTitle
    #     self.liveBroadcastContent = liveBroadcastContent

    
# @dataclass
# class SearchResourceId(Base):
#     __tablename__ = "search_resource_id"

#     pk = Column(Integer, primary_key=True, autoincrement=True)

#     kind = Column(String)
#     videoId = Column(String)
#     channelId = Column(String)
#     playlistId = Column(String)
#     snippets = Relationship("Snippet", back_populates="searchResourceId", uselist=True)  #List[Snippet]

#     searchResource_fk: Mapped[int] = mapped_column(ForeignKey("search_resources.pk")) #Column(Integer, ForeignKey("search_resources.pk"))
#     searchResource: [Mapped["SearchResource"]] = relationship(back_populates="id") #Relationship("SearchResource", back_populates="id")


# @dataclass
# class SearchResource(Base):
#     __tablename__ = "search_resources"

#     pk = Column(Integer, primary_key=True, autoincrement=True)

#     kind = Column(String)
#     etag = Column(String)
#     # id: Mapped[List["SearchResourceId"]] = relationship(back_populates="searchResource")#Relationship("SearchResourceId", back_populates="searchResourceId", uselist=True)  #List[SearchResourceId]

#     response_fk: Mapped[int] =  mapped_column(ForeignKey("response.pk")) #Column(Integer, ForeignKey("responses.pk"))
#     response: Mapped["Response"] = relationship(back_populates="items")#Relationship("Response", back_populates="items")
    

@dataclass
class PageInfo(Base):
    __tablename__ = "page_infos"

    pk = Column(Integer, primary_key=True, autoincrement=True)

    totalResults = Column(Integer)
    resultsPerPage = Column(Integer)

    response_fk = Column(Integer, ForeignKey("responses.pk")) #: Mapped[int] = mapped_column(ForeignKey("responses.pk"))
    response = Relationship("Response", back_populates="pageInfos")#: Mapped["Response"] = relationship(back_populates="pageInfos")
    
    def __repr__(self) -> str:
        return (f"PageInfo(totalResults={self.totalResults}, resultsPerPage={self.resultsPerPage})")

    def __init__(self, totalResults, resultsPerPage):
        self.totalResults = totalResults
        self.resultsPerPage = resultsPerPage
        print(self)


@dataclass
class Response(Base):
    __tablename__ = "responses"

    pk = Column(Integer, primary_key=True, autoincrement=True)

    kind = Column(String)
    etag = Column(String)
    nextPageToken = Column(String)
    # prevPageToken = Column(String) #TODO prevPageToken seems to be missing in API response
    regionCode = Column(String)
    pageInfos = Relationship("PageInfo", back_populates="response")#: Mapped[List["PageInfo"]] = relationship(back_populates="response") #List[PageInfo]
    # items: Mapped[List["SearchResource"]] = relationship(back_populates="response")#Relationship("SearchResource", back_populates="response")#List[SearchResource]

    def __repr__(self):
        return (f"Response(kind={self.kind}, etag={self.etag}, nextPageToken={self.nextPageToken}, regionCode={self.regionCode}, pageInfos={self.pageInfos})")

    def __init__(self, kind, etag, nextPageToken, regionCode, pageInfo, items):
        self.kind = kind
        self.etag = etag
        self.nextPageToken = nextPageToken
        self.regionCode = regionCode
        self.pageInfo = pageInfo
        self.items = items
        print(self)
    
    def __post_init__(self): #https://www.youtube.com/watch?v=Fu0swCLAJ8E
        self.pageInfos = [PageInfo(**pageInfo) for pageInfo in self.pageInfos]
        print(self)
    #     session.add(self)



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


        session.add(self.response)
        session.commit()
        session.close()

        

search = Search(q="airport ambiance noise", type = "video", eventType = "completed")
search.execute()