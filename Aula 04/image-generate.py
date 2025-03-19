import streamlit as st
from PIL import Image
import requests
import base64
from io import BytesIO

# Configurações da API
API_URL = "https://api.cloudflare.com/client/v4/accounts/f4558c94b684c585ace3162d9b5f7c9b/ai/run/@cf/black-forest-labs/flux-1-schnell"
HEADERS = {
    "Authorization": "Bearer aPoBuP_v5yluyAE1YU5mZJ1DuqoL5QVeErq4F29I",
    "Content-Type": "application/json"
}

# Página
st.set_page_config(page_title="Gerador de Imagens com IA", layout="centered")
st.title("🎨 Gerador de Imagens com AI")

# Prompt
prompt = st.text_input("Digite o prompt da imagem que deseja gerar:")

# Botão gerar
if st.button("✨ Gerar Imagem"):
    if prompt.strip():
        with st.spinner("Gerando imagem..."):
            data = {
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 30
            }
            try:
                response = requests.post(API_URL, json=data, headers=HEADERS)
                if response.status_code == 200:
                    image_base64 = response.json()["result"]["image"]
                    image_data = base64.b64decode(image_base64)
                    image = Image.open(BytesIO(image_data))

                    st.image(image, caption="Imagem gerada", use_column_width=True)

                    # Botão de download
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    b64 = base64.b64encode(buffered.getvalue()).decode()
                    href = f'<a href="data:file/png;base64,{b64}" download="imagem_gerada.png">💾 Baixar imagem</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.error(f"Erro ao gerar imagem: {response.status_code}\n{response.text}")
            except Exception as e:
                st.error(f"Erro ao processar a imagem: {e}")
    else:
        st.warning("Digite um prompt antes de gerar a imagem.")
