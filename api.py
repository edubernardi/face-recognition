from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from PIL import Image
import io
import uuid
import numpy as np
import face_recognition
from database import add_image_record, add_history_record, get_all_face_encodings

app = FastAPI()

# Cria diretórios para armazenar imagens caso ainda não existirem localmente
IMAGE_FOLDER = "images"
SEARCH_FOLDER = "search_images"

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(SEARCH_FOLDER, exist_ok=True)

@app.post("/cadastrar/")
async def upload_image(file: UploadFile = File(...), username: str = "Nulo"):
    # Verifica extensão do arquivo
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in {'.jpg', '.jpeg', '.png'}:
        raise HTTPException(status_code=400, detail="Extensão inválida")

    # Verifica se o arquivo é uma imagem válida
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
    except:
        raise HTTPException(status_code=400, detail="Imagem inválida")

    # Gera id único de 8 caracteres para a imagem
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{unique_id}{file_ext}"
    filepath = os.path.join(IMAGE_FOLDER, filename)
    
    # Salva a imagem localmente
    image.save(filepath)
    
    # Utiliza a biblioteca face_recognition para obter codificação facial da imagem salva
    face_encodings = face_recognition.face_encodings(face_recognition.load_image_file(filepath))
    
    # Converte a codificação para bytes para armazenamento no banco de dados
    face_encoding_bytes = face_encodings[0].tobytes() if len(face_encodings) > 0 else None
    
    # Salva o cadastro no banco de dados
    add_image_record(username, filepath, face_encoding_bytes)
    
    return {
        "filename": filename,
        "username": username,
        "faces_detected": len(face_encodings)
    }

@app.post("/identificar/")
async def search_faces(file: UploadFile = File(...)):
    
    
    # Verifica extensão do arquivo
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in {'.jpg', '.jpeg', '.png'}:
        raise HTTPException(status_code=400, detail="Extensão inválida")

    # Verifica se o arquivo é uma imagem válida
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
    except:
        raise HTTPException(status_code=400, detail="Imagem inválida")

    # Gera id único de 8 caracteres para a imagem e a salva localmente
    search_filename = f"identifica_{str(uuid.uuid4())[:8]}{file_ext}"
    filepath = os.path.join(SEARCH_FOLDER, search_filename)
    image.save(filepath)
    
    # Utiliza a biblioteca face_recognition para obter codificação facial da imagem salva
    face_encodings = face_recognition.face_encodings(face_recognition.load_image_file(filepath))
    
    if not face_encodings:
        add_history_record(filepath)  # Não foram encontrados rostos na imagem
        return {
            "status": "no_faces",
            "search_path": filepath
        }
    
    search_encoding = face_encodings[0]  # Seleciona a primeira face da imagem se tiver mais de uma
    
    # Carrega todas as codificações faciais conhecidas do banco de dados
    known_faces = get_all_face_encodings()
    
    # Itera por todas as faces conhecidas comparando com a face sendo avaliada
    for face in known_faces:
        matches = face_recognition.compare_faces(
            [face['face_encoding']], 
            search_encoding,
            tolerance=0.6
        )
        
        if matches[0]:
            # Calcula a confiança, que é inversamente proporcional à distância entre as codificações faciais
            face_distance = face_recognition.face_distance(
                [face['face_encoding']], 
                search_encoding
            )[0]
            confidence = 1 - face_distance
            
            # Adiciona a busca aos registros de histórico
            add_history_record(
                filepath,
                face['id'],
                face['username'],
                float(confidence)
            )
            return {
                "status": "match_found",
                "matched_username": face['username'],
                "confidence": float(confidence),
                "filepath": filepath,
                "matched_image_id": face['id']
            }
    
    add_history_record(filepath)
    return {
        "status": "no_match",
        "filepath": filepath
    }
