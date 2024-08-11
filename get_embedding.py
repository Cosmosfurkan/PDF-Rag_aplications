from langchain_community.embeddings.bedrock import BedrockEmbeddings # AWS embedding model

def create_embeding_Bedrock():
    embedding = BedrockEmbeddings(
        credentials_profile_name='bedrock-admin',
        region_name='us-west-1',
    )
    return embedding

# def create_embeding_ollama():
#     embedding = OllamaEmbeddings(
#         model="nomic-embed-text"
#     )
#     return embedding # only use in linux os
