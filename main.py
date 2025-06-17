import streamlit as st
import os
import requests
from PIL import Image
import time
from database import get_recent_images, get_recognition_history
import sqlite3

API_ENDPOINT = "http://localhost:8000/"

st.title("Serviço de Reconhecimento Facial IOT")

st.header("Cadastrar Usuário")

username = st.text_input("Usuário", "Usuário")

uploaded_file = st.file_uploader("Escolha uma imagem com rosto do usuário...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagem enviada", use_container_width=True)
        
        files = {
            "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        
        proxies = {
            "http": "http://127.0.0.1:8080",
            "https": "http://127.0.0.1:8080"
        }
        params = {"username": username}
        response = requests.post(f"{API_ENDPOINT}cadastrar/", files=files, params=params, proxies=proxies, verify=False)
        
        if response.status_code == 200:
            st.success("Imagem cadastrada com sucesso!")
        else:
            st.error(f"Falha ao enviar imagem, código: {response.status_code}")
    except Exception as e:
        st.error(f"Erro ao processar imagem: {str(e)}")

st.header("Usuário cadastrados")

try:
    recent_images = get_recent_images(100)
    
    if not recent_images:
        st.info("Nenhum cadastro até o momento.")
    else:
        cols = st.columns(2)
        for idx, img_data in enumerate(recent_images):
            with cols[idx % 2]:
                try:
                    if os.path.exists(img_data['filepath']) and img_data['face_encoding'] is not None:
                        img = Image.open(img_data['filepath'])
                        caption = f"Usuário: {img_data['username']}\n{os.path.basename(img_data['filepath'])}"
                        
                        st.image(img, 
                               caption=caption,
                               use_container_width=True)
                    else:
                        st.error(f"Imagem não encontrada: {img_data['filepath']}")
                except Exception as e:
                    st.error(f"Erro ao carregar a imagem: {img_data['filepath']}: {e}")
except Exception as e:
    st.error(f"Erro ao acessar as imagens: {str(e)}")

st.header("Identificar Usuário")

search_file = st.file_uploader("Envie imagem para identificar usuário...", type=["jpg", "jpeg", "png"])

if search_file is not None:
    try:
        # Display the search image
        search_image = Image.open(search_file)
        st.image(search_image, caption="Search Image", use_container_width=True)

        # Prepare and send to API
        files = {"file": (search_file.name, search_file.getvalue(), search_file.type)}
        response = requests.post(f"{API_ENDPOINT}identificar/", files=files)
        
        if response.status_code == 200:
            result = response.json()
            
            if result['status'] == "match_found":
                st.success(f"Correspondência encontrada com usuário {result['matched_username']} (confiança: {result['confidence']:.2%})")
            elif result['status'] == "no_match":
                st.warning("Não foi possível encontrar correspondência para o usuário na imagem enviada.")
            else:
                st.info("Não foram detectados rostos na imagem enviada.")
                                
        else:
            st.error(f"Erro na busca, código: {response.status_code}")
            
    except Exception as e:
        st.error(f"Erro processando a busca: {str(e)}")

st.header("Histórico de Reconhecimento")

try:
    history = get_recognition_history()
    
    if not history:
        st.info("Sem nenhum registro no histórico.")
    else:
        for entry in history:
            with st.expander(f"Busca em {entry['timestamp']}", expanded=False):
                cols = st.columns([1, 2])
                
                with cols[0]:
                    if os.path.exists(entry['search_image']):
                        st.image(
                            Image.open(entry['search_image']),
                            caption="Imagem avaliada",
                            use_container_width=True
                        )
                    else:
                        st.error("Imagem não encontrada")
                
                with cols[1]:
                    if entry['matched_image_id']:
                        if os.path.exists(entry['matched_image_path']):
                            st.image(
                                Image.open(entry['matched_image_path']),
                                caption=f"Matched: {entry['matched_username']}",
                                use_container_width=True
                            )
                        else:
                            st.error("Imagem não encontrada")
                        
                        st.progress(float(entry['confidence']))
                        st.write(f"Confiança: {float(entry['confidence']):.2%}")
                        st.write(f"ID da Correspondência: {entry['matched_image_id']}")
                    else:
                        st.warning("Sem correspondência encontrada")
                
except Exception as e:
    st.error(f"Erro carregando o histórico: {str(e)}")