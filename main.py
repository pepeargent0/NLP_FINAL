# !pip install llama-index-embeddings-huggingface==0.1.1 sentence-transformers==2.3.1 pypdf==4.0.1 langchain==0.1.7 python-decouple==3.8
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from jinja2 import Template
import requests
from decouple import config
from llama_index.core import Settings

def zephyr_instruct_template(messages, add_generation_prompt=True):
    # Definir la plantilla Jinja
    template_str = "{% for message in messages %}"
    template_str += "{% if message['role'] == 'user' %}"
    template_str += "<|user|>{{ message['content'] }}</s>\n"
    template_str += "{% elif message['role'] == 'assistant' %}"
    template_str += "<|assistant|>{{ message['content'] }}</s>\n"
    template_str += "{% elif message['role'] == 'system' %}"
    template_str += "<|system|>{{ message['content'] }}</s>\n"
    template_str += "{% else %}"
    template_str += "<|unknown|>{{ message['content'] }}</s>\n"
    template_str += "{% endif %}"
    template_str += "{% endfor %}"
    template_str += "{% if add_generation_prompt %}"
    template_str += "<|assistant|>\n"
    template_str += "{% endif %}"

    # Crear un objeto de plantilla con la cadena de plantilla
    template = Template(template_str)

    # Renderizar la plantilla con los mensajes proporcionados
    return template.render(messages=messages, add_generation_prompt=add_generation_prompt)


# Aquí hacemos la llamada el modelo
def generate_answer(prompt: str, max_new_tokens: int = 768) -> None:
    try:
        # Tu clave API de Hugging Face. Busca en el .env, luego en los secretos de Google Colab
        api_key = config('HUGGINGFACE_TOKEN', userdata.get('HUGGINGFACE_TOKEN'))

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

# Esta función prepara el prompt en estilo QA
def prepare_prompt(query_str: str, context_str: str):
  TEXT_QA_PROMPT_TMPL = (
      "La información de contexto es la siguiente:\n"
      "---------------------\n"
      "{context_str}\n"
      "---------------------\n"
      "Dada la información de contexto anterior, y sin utilizar conocimiento previo, responde la siguiente pregunta.\n"
      "Pregunta: {query_str}\n"
      "Respuesta: "
  )

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
model_name = "sentence-transformers/distiluse-base-multilingual-cased-v2"
#model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#model_name = "sentence-transformers/LaBSE"
embed_model = HuggingFaceEmbedding(model_name=model_name)

print('Indexando documentos...')
# Carga los documentos de la carpeta y luego genera e indexa los embeddings
documents = SimpleDirectoryReader("llamaindex_data").load_data()
# Construimos un índice de documentos a partir de los datos de la carpeta llamaindex_data
index = VectorStoreIndex.from_documents(documents, show_progress=True, embed_model=embed_model)

# Construimos un retriever a partir del índice, para realizar la búsqueda vectorial de documentos
retriever = index.as_retriever(similarity_top_k=2)

print('Realizando llamada a HuggingFace para generar respuestas...\n')

queries = ['¿Que pasó en la crisis del 29?',
           '¿Cuándo se redactó la constitución Argentina?',
           '¿Cuándo fué la revolución de Mayo?',
           '¿Cuándo se declaró la independencia?',
           '¿Cuándo asumió Raúl Alfonsín como presidente?']

for query_str in queries:
    # Traemos los documentos más relevantes para la consulta
    nodes = retriever.retrieve(query_str)
    print('node')
    # Construimos el contexto para usar con el LLM
    context_str = ''
    for node in nodes:
        page_label = node.metadata["page_label"]
        file_path = node.metadata["file_path"]
        context_str += f"\npage_label: {page_label}\n"
        context_str += f"file_path: {file_path}\n\n"
        context_str += f"{node.text}\n"
    #print(f'context_str: {context_str}')

    final_prompt = prepare_prompt(query_str, context_str)
    print('Pregunta:', query_str)
    print('Respuesta:')
    print(generate_answer(final_prompt))
    print('-------------------------------------------------------')