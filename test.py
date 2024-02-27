from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.embeddings import GPT4AllEmbeddings
import nltk
import ssl
import time

# Descarga de recursos de nltk
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# nltk.download('averaged_perceptron_tagger')

# Configuración del modelo de incrustación de oraciones
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Carga de documentos desde un directorio
loader = DirectoryLoader("data_text")
documents = loader.load()

# División de documentos en fragmentos
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=40,
)

print('Comenzando a cargar y dividir documentos...')
start_time = time.time()

# División de documentos en fragmentos
chunked_docs = splitter.split_documents(documents)

end_time = time.time()
print('Tiempo para cargar y dividir documentos:', end_time - start_time, 'segundos')

# Configuración del modelo de incrustación
# embedder = GPT4AllEmbeddings()

# Creación del vector store
vector_db = Chroma(
    persist_directory='croma_db',
    embedding_function=embedding_function
)

print('Instanciando el modelo y creando el vector store...')
start_time = time.time()

# Inserción de los fragmentos de documentos en el vector store
vector_db.add_documents(chunked_docs)

# Persistencia del vector store
vector_db.persist()

end_time = time.time()
print('Tiempo para instanciar el modelo y crear el vector store:', end_time - start_time, 'segundos')

# Búsqueda de similitud
query = "exploit para windows"
print('Realizando búsqueda de similitud...')
start_time = time.time()

docs = vector_db.similarity_search(query)

end_time = time.time()
print('Tiempo para realizar la búsqueda de similitud:', end_time - start_time, 'segundos')

print(len(docs), docs)
