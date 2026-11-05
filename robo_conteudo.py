import os
import random
import time
import requests
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOG_ID = os.environ.get("BLOG_ID")
B_CLIENT_ID = os.environ.get("B_CLIENT_ID")
B_CLIENT_SECRET = os.environ.get("B_CLIENT_SECRET")
B_REFRESH_TOKEN = os.environ.get("B_REFRESH_TOKEN")

client = genai.Client(api_key=GEMINI_API_KEY)

CATEGORIAS = ['Bolsa & Ações', 'Criptomoedas', 'Câmbio & Forex', 'Análises & Economia']

# Pools dedicados de imagens de alta qualidade do Unsplash para cada categoria (sem repetição)
IMAGENS_POR_CATEGORIA = {
    'Bolsa & Ações': [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=85"
    ],
    'Criptomoedas': [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&w=1200&q=85"
    ],
    'Câmbio & Forex': [
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1580519542036-c47de6196ba5?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=85"
    ],
    'Análises & Economia': [
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1200&q=85"
    ]
}

def obter_imagem_hd(categoria):
    """Seleciona uma imagem condizente e rotativa com base na categoria escolhida"""
    lista_imgs = IMAGENS_POR_CATEGORIA.get(categoria, IMAGENS_POR_CATEGORIA['Análises & Economia'])
    return random.choice(lista_imgs)

def obter_novo_access_token():
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": B_CLIENT_ID,
        "client_secret": B_CLIENT_SECRET,
        "refresh_token": B_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def gerar_artigo():
    cat_escolhida = random.choice(CATEGORIAS)

    prompt = f"""
    Você é um jornalista e editor visual sênior para o portal 'Crypto & Mercado'.
    Escreva um artigo rico, cativante e altamente informativo sobre '{cat_escolhida}'.

    ESTRUTURA OBRIGATÓRIA (HTML):
    [TITULO] Título impressionante e otimizado para SEO [/TITULO]
    [CONTEUDO]
    <p class="lead"><b>Introdução envolvente destacando o valor visual e a importância do tema...</b></p>
    <h3>Destaques e Análise Técnica</h3>
    <p>Explicação aprofundada com detalhes visuais e contextuais...</p>
    <h3>Conclusão e Tendências</h3>
    <p>Considerações finais para os leitores...</p>
    <br><hr>
    <p><small><i><b>Disclaimer:</b> Conteúdo informativo e educacional.</i></small></p>
    [/CONTEUDO]
    """

    for tentativa in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            texto = response.text
            
            # Extração segura com validação
            if "[TITULO]" in texto and "[/TITULO]" in texto and "[CONTEUDO]" in texto and "[/CONTEUDO]" in texto:
                titulo = texto.split("[TITULO]")[1].split("[/TITULO]")[0].strip()
                conteudo = texto.split("[CONTEUDO]")[1].split("[/CONTEUDO]")[0].strip()
            else:
                # Fallback caso a IA ignore alguma tag
                titulo = f"Análise Especializada de Mercado: {cat_escolhida}"
                conteudo = f"<p class='lead'><b>Panorama atualizado sobre os movimentos recentes em {cat_escolhida}.</b></p><p>{texto}</p>"

            imagem_url = obter_imagem_hd(cat_escolhida)
            html_final = f'<div class="article-hero"><img src="{imagem_url}" alt="{titulo}" style="width:100%; max-height:500px; object-fit:cover; border-radius:12px; margin-bottom:20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);"/></div>\n' + conteudo

            return titulo, html_final, cat_escolhida
        except Exception as e:
            print(f"⚠️ Servidor ocupado (Tentativa {tentativa+1}/3). A tentar novamente em 10 segundos... Erro: {e}")
            time.sleep(10)
    
    raise Exception("Falha ao gerar artigo após 3 tentativas devido à alta demanda do modelo.")

def publicar():
    access_token = obter_novo_access_token()
    if not access_token:
        print("❌ Erro ao renovar o Access Token do Blogger.")
        return

    titulo, conteudo, etiqueta = gerar_artigo()
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {"kind": "blogger#post", "title": titulo, "content": conteudo, "labels": [etiqueta, "Crypto & Mercado"]}

    res = requests.post(url, json=payload, headers=headers)
    if res.status_code == 200:
        print(f"✅ Publicado com sucesso: [{etiqueta}] {titulo}")
    else:
        print(f"❌ Erro ao publicar: {res.text}")

if __name__ == "__main__":
    publicar()
