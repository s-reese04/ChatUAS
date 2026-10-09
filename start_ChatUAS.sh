#!/bin/bash

docker start qdrant

python setUp_Qdrant.py
python rag_app.py
