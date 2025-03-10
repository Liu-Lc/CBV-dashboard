# set base image (host OS)
FROM python:3.8.0

# set the working directory in the container
WORKDIR /cbv-data

# copy the dependencies file to the working directory
COPY requirements.txt .
# install dependencies
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# command to run on container start
CMD [ "python", "index.py"]
