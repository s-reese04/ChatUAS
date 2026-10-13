#!/bin/bash

docker start qdrant

python scrape.py
python setUp_Qdrant.py

uvicorn api:app --host 127.0.0.1 --port 8001
