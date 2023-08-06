FROM python:latest
EXPOSE 8000
RUN apt-get -y install git
RUN git clone https://github.com/CrowdCurio/audio-annotator.git
CMD ["python3", "-m" , "http.server", "-d", "audio-annotator"]