# Use an official Python runtime as a parent image
FROM continuumio/miniconda3

RUN apt-get update
RUN apt-get install -y build-essential 

RUN mkdir /tmp/ndexnetworktrim
COPY ./ /tmp/ndexnetworktrim/
RUN pip install /tmp/ndexnetworktrim

RUN rm -rf /tmp/ndexnetworktrim

RUN mkdir /ndexnetworktrim
WORKDIR /ndexnetworktrim

CMD /bin/echo "To use run: ndexnetworktrim.py"
