"""
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from decouple import config
from llama_index import ServiceContext, VectorStoreIndex, download_loader, SimpleDirectoryReader



from jinja2 import Template
import requests
from decouple import config
import nltk
import pandas as pd

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt')

def zephyr_instruct_template(messages, add_generation_prompt=True):
    # Definir la plantilla Jinja
    template_str = "{% for message in messages %}"
    template_str += "{% if message['role'] == 'user' %}"
    template_str += "{{ message['content'] }}</s>\n"
    template_str += "{% elif message['role'] == 'assistant' %}"
    template_str += "{{ message['content'] }}</s>\n"
    template_str += "{% elif message['role'] == 'system' %}"
    template_str += "{{ message['content'] }}</s>\n"
    template_str += "{% else %}"
    template_str += "{{ message['content'] }}</s>\n"
    template_str += "{% endif %}"
    template_str += "{% endfor %}"
    template_str += "{% if add_generation_prompt %}"
    template_str += "\n"
    template_str += "{% endif %}"
    # Crear un objeto de plantilla con la cadena de plantilla
    template = Template(template_str)
    # Renderizar la plantilla con los mensajes proporcionados
    return template.render(messages=messages, add_generation_prompt=add_generation_prompt)


def generate_answer(prompt: str, max_new_tokens: int = 768) -> str:
    try:
        # Tu clave API de Hugging Face
        api_key = config('HF_API_KEY')
        # api_key = config('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')
        # URL de la API de Hugging Face para la generación de texto
        api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
        # Cabeceras para la solicitud
        headers = {"Authorization": f"Bearer {api_key}"}
        # Datos para enviar en la solicitud POST
        # Sobre los parámetros: https://huggingface.co/docs/transformers/main_classes/text_generation
        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": 0.7,
                "top_k": 50,
                "top_p": 0.95
            }
        }
        # Realizamos la solicitud POST
        response = requests.post(api_url, headers=headers, json=data)
        # Extraer respuesta
        respuesta = response.json()[0]["generated_text"][len(prompt):]
        return respuesta
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


def prepare_prompt(query_str: str, nodes: list):
    TEXT_QA_PROMPT_TMPL = (
        "La información de contexto es la siguiente:\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Dada la información de contexto anterior, y sin utilizar conocimiento previo, responde la siguiente pregunta.\n"
        "Pregunta: {query_str}\n"
        "Respuesta: "
    )

    # Construimos el contexto de la pregunta
    context_str = ''
    for node in nodes:
        # Usamos get para obtener la clave, y si no está presente, proporcionamos un valor predeterminado
        page_label = node.metadata.get("page_label", "No Page Label")
        file_path = node.metadata.get("file_path", "No File Path")
        context_str += f"\npage_label: {page_label}\n"
        context_str += f"file_path: {file_path}\n\n"
        context_str += f"{node.text}\n"

    messages = [
        {
            "role": "system",
            "content": "Eres un asistente útil que siempre responde con respuestas veraces, útiles y basadas en hechos.",
        },
        {"role": "user", "content": TEXT_QA_PROMPT_TMPL.format(context_str=context_str, query_str=query_str)},
    ]
    final_prompt = zephyr_instruct_template(messages)
    return final_prompt


# Cargamos nuestro modelo de embeddings
print('Cargando modelo de embeddings...')
embed_model = HuggingFaceEmbeddings(model_name='sentence-transformers/paraphrase-multilingual-mpnet-base-v2')


# Construimos un índice de documentos a partir del archivo CSV con delimitador "|"
print('Indexando documentos...')

df = pd.read_csv("data/segu-info.csv", encoding="utf-8", delimiter='|', nrows=800)

# Obtener los valores de las columnas "title" y "text"
titles = df["title"].tolist()
texts = df["text"].tolist()

# Combinar títulos y textos en un solo texto, separando con '\n'
combined_text = "\n".join(f"{title}\n{text}" for title, text in zip(titles, texts))

# Guardar el texto combinado en un archivo
with open("data_text/combined_text.txt", "w", encoding="utf-8") as file:
    file.write(combined_text)

documents = SimpleDirectoryReader("data_text").load_data()
index = VectorStoreIndex.from_documents(documents, show_progress=True, service_context=ServiceContext.from_defaults(embed_model=embed_model, llm=None))
retriever = index.as_retriever(similarity_top_k=2)

# Realizando llamada a HuggingFace para generar respuestas...
queries = ['¿Que es logofail?', 'cuales son las claves mas usadas','me explicas como explotar una vulnerabilidad',
           'me enumeras 5 vulnerabiliades de codigo remoto', 'que es google hacking']
for query_str in queries:
    # Traemos los documentos más relevantes para la consulta
    nodes = retriever.retrieve(query_str)
    final_prompt = prepare_prompt(query_str, nodes)
    print('Pregunta:', query_str)
    print('Respuesta:')
    print(generate_answer(final_prompt))

"""
import pandas as pd
from data_base.data_base import Neo4jDataLoader
from source_data.main import DataPrep

if __name__ == '__main__':
    # get_data = DataPrep().download_and_process_data()   #esta funcion se encarga de conseguir los datos atravez de scrapper


    # Rutas a tus archivos CSV
    csv_cve_path = 'data/cve_data.csv'
    csv_exploit_path = 'data/exploit_db.csv'
    csv_news_path = 'data/segu-info.csv'

    df_cve = pd.read_csv(csv_cve_path, encoding='latin-1')
    print(df_cve.columns)
    df_exploit = pd.read_csv(csv_exploit_path)
    df_news = pd.read_csv(csv_news_path, delimiter='|')

    neo4j_loader = Neo4jDataLoader(uri, user, password)

    # Crear nodos y relaciones en una transacción
    neo4j_loader.create_nodes(df_cve, df_exploit, df_news)
    neo4j_loader.create_relationships()

    # Cierra la conexión al finalizar
    neo4j_loader.close()