FROM python:3.12-bookworm

RUN pip install --upgrade pip

ENV APP /app
RUN mkdir $APP
WORKDIR $APP

# Copy the requirements file in order to install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt && pip freeze

# Copy the rest of the codebase into the image
COPY . $APP

# Expose the port uWSGI will listen on
ENV PORT 80
EXPOSE $PORT

# Finally, we run uvicorn with the main file
CMD python -m app.main