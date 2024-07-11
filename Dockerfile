FROM python:slim

WORKDIR /app

COPY . .

RUN pip install --upgrade -r requirements.txt && pip cache purge 

# Flask
CMD ["sh", "launch_app.sh"]
EXPOSE 5601 3000
