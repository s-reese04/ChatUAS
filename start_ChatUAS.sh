#!/bin/bash

docker start qdrant

python scrape.py
python setUp_Qdrant.py
python rag_app.py
