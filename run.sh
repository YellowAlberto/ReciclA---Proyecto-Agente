#!/bin/bash

# Iniciar FastAPI 
uvicorn ProyectoBasura:app --host 0.0.0.0 --port 8000 &

sleep 5

# Iniciar frontend
python app_front.py