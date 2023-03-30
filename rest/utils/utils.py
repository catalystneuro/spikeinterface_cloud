from typing import List, Union
from io import BytesIO
from pypdf import PdfReader
from uuid import uuid4
import docx
import re
import tiktoken
from langchain.text_splitter import TokenTextSplitter

from clients.qdrant import QdrantCustomClient
from clients.cohere import CohereClient
from clients.openai import OpenaiClient
from clients.db import DatabaseClient


def create_persona(
    user_id: str,
    files: List, 
    ref_name: str, 
    name: str, 
    user_provided_qualities: str, 
    avatar: str
) -> str:
    try:
        # db_client = DatabaseClient(connection_string="")
        # persona = db_client.create_persona(user_id=user_id, ref_name=ref_name, name=name, user_provided_qualities=user_provided_qualities, avatar=avatar)
        all_texts = extract_texts_from_all_files(files=files)
        excerpts_objects = []
        for text in all_texts:
            # document_metadata = extract_metadata_from_text_content(text_content)
            # document = db_client.create_document(persona_id=persona.id, **document_metadata)
            all_excerpts = text_splitter(
                text=text, 
                chunk_size=1200, 
                chunk_overlap=50, 
                encoding_for_model="text-curie-001"
            )
            for ii, ex in enumerate(all_excerpts):
                # excerpt = db_client.create_excerpt(document_id=document.id, index=ii, text=ex)
                # This will be used to populate the Vector DB metadata later on
                excerpts_objects.append({
                    "text": ex.text,
                    "persona_name": name,
                    "vector": None,
                })
        
        # Get the characteristics of the Persona from the excerpts
        characteristics = get_characteristics_from_excerpts(texts=all_texts)

        # Update the Persona with the characteristics extracted from the texts
        updated_user = db_client.update_object_property(persona, "characteristics", characteristics)
        
        # Vectorize all excerpts
        # updated_excerpts_objects = vectorize_excerpts(excerpts_objects=excerpts_objects)
        
        # Add excerpts to Vector DB
        # add_excerpts_to_qdrant(excerpts_objects=updated_excerpts_objects)
        return {"status": "ok", "error": None}
    except Exception as e:
        return {"status": "error", "error": e}


def get_persona_characteristics_from_excerpts(texts: list, persona_name: str, is_narrator: bool, model: str = "text-babbage-001") -> str:
    openai_client = OpenaiClient()
    if is_narrator:
        persona_name = "the Narrator"
    
    all_responses = []
    for text in texts:
        all_excerpts = text_splitter(
            text=text, 
            chunk_size=1400, 
            chunk_overlap=0, 
            encoding_for_model=model
        )
        for excerpt in all_excerpts:
            prompt = f"""excerpt: {excerpt}
---
From the given excerpt, extract the characteristics of {persona_name}. 
Those can be physical, mental or emotional attributes, things they like or dislike, or any other quality that you can think of.
If you can't think of any, just say "None".
Begin: {persona_name} is"""
            response = openai_client.get_completion(
                prompt=prompt,
                model=model,
                max_tokens=300,
                temperature=0.1,
            )
            all_responses.append(response)

    combined_responses = " ".join(all_responses)
    combined_responses = cap_text_length_in_tokens(text=combined_responses, max_length=3000, encoding_for_model="gpt-3.5-turbo")
    prompt = f"""Character's info: {combined_responses}
Given the above info, make bullet points listing the characteristics of {persona_name}
Try to describe both things that are positive (likes, gives them positive feelings) and also things that are negative (dislikes, gives them negative feelings) for {persona_name}
The list should contain between 8 and 12 points
Make just one single sentence for each point
Begin:"""
    final_response = openai_client.get_completion(
        prompt=prompt,
        model="gpt-3.5-turbo",
        max_tokens=600,
        temperature=0.1,
    )
    return {
        "all_responses": all_responses,
        "final_response": final_response
    }


def vectorize_excerpts(excerpts_objects: list) -> list:
    # Get Cohere embeddings
    texts = [ex["text"] for ex in excerpts_objects]
    cohere_client = CohereClient()
    embeddings = cohere_client.get_embeddings(texts=texts)
    for ii, ex in enumerate(excerpts_objects):
        ex["vector"] = embeddings[ii]
    return excerpts_objects


def add_excerpts_to_qdrant(excerpts_objects: list) -> None:
    # Add to Qdrant    
    ids = []
    payloads = []
    vectors = []
    for ii, obj in enumerate(excerpts_objects):
        ids.append(str(uuid4()))
        vector = obj.pop("vector")
        vectors.append(vector)
        obj["order_position"] = ii
        payloads.append(obj)
    qdrant_client = QdrantCustomClient(collection_name="persona")
    try:
        qdrant_client.insert_items_batch(ids=ids, payloads=payloads, vectors=vectors)
        return None
    except Exception as e:
        raise e


def talk_to_character(
        question: str, 
        character_name: str, 
        character_description: str,
        llm_model: str = "gpt-3.5-turbo",
        llm_temperature: float = 0.1,
        llm_max_tokens: int = 200
    ):
    embedding = get_embedding(question)
    relevant_excerpts = get_qdrant_results(search_embedding=embedding)
    prompt = prompt_talk_to_character(question, relevant_excerpts, character_name, character_description)
    return get_llm_response(prompt=prompt, model=llm_model, temperature=llm_temperature, max_tokens=llm_max_tokens)


def prompt_talk_to_character(question: str, relevant_excerpts: List[str], character_name: str, character_description: str):
    excerpts = ""
    for r in relevant_excerpts:
        excerpts += f"""
    excerpt: {r.payload.get('text')}"""

    prompt = f"""You are {character_name}, you should always answer as {character_name}. 
Here's a list of things you find positive and negative:
{character_description}

Consider the excerpts below:
{excerpts}

Your mood today is: a bit anxious

Taking all that into consideration, answer this question:
Question: {question}

Do not include your name in the answer.
Answer:"""
    return prompt


def extract_texts_from_all_files(files: list) -> list:
    texts = []
    for file in files:
        file_contents = file.read()
        file_bytes = BytesIO(file_contents)
        texts.append(extract_text_from_file(file_bytes, content_type=file.content_type))
    return texts


def extract_text_from_file(file_bytes: BytesIO, content_type: str) -> str:
    if content_type == "text/plain":
        text = extract_text_from_txt(file_bytes)
    elif content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_docx(file_bytes)
    else:
        raise Exception(f"Unsupported file type: {content_type}")
    return text


def extract_text_from_txt(file: BytesIO) -> str:
    return file.read().decode("utf-8")


def extract_text_from_pdf(file: Union[BytesIO, str]) -> str:
    reader = PdfReader(file)
    pages_list = [p for p in reader.pages]
    full_text = " ".join([p.extract_text().replace("\n", " ").replace("..", "") for p in pages_list])
    full_text = re.sub(r'\s+', ' ', full_text)  # Remove long sequences of spaces
    return full_text


def extract_text_from_docx(file: Union[BytesIO, str]) -> str:
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text
    return text


def cap_text_length_in_tokens(text: str, max_length: int = 1400, cap_from: str = "end", encoding_for_model: str = "text-curie-001") -> str:
    encoding = tiktoken.encoding_for_model(encoding_for_model)
    encoded_tokens = encoding.encode(text=text)
    if len(encoded_tokens) <= max_length:
        return text
    else:
        if cap_from == "start":
            return encoding.decode(encoded_tokens[-max_length:])
        else:
            return encoding.decode(encoded_tokens[0:max_length])


def text_splitter(text: str, chunk_size: int = 1200, chunk_overlap: int = 50, encoding_for_model: str = "text-curie-001"):
    encoding = tiktoken.encoding_for_model(encoding_for_model)
    text_splitter = TokenTextSplitter(encoding_name=encoding.name, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(text)


def get_sentences_from_full_text(full_text: str, max_length: int=2000) -> list:
    sentences = full_text.split(". ")
    if len(sentences) == 1:
        return sentences
    sentences_list = list()
    last_sentence = sentences[0]
    for i, s in enumerate(sentences[1:]):
        combined_sentence = last_sentence + ". " + s
        if len(combined_sentence) > max_length:
            sentences_list.append(last_sentence.strip())
            last_sentence = s
        else:
            last_sentence = combined_sentence
            if i == len(sentences) - 2:
                sentences_list.append(last_sentence.strip())
    return sentences_list


def extract_metadata_from_text_content(text_content: str) -> dict:
    prompt = f"""Given the text below, extract these three pieces of information: 
1) title: 
2) author: 
3) publication year: (should be just a number)

Text:
{text_content}

Information:"""

    openai_client = OpenaiClient()

    response = openai_client.get_completion(
        model="gpt-3.5-turbo",
        prompt=prompt,
        temperature=0.1,
        max_tokens=100,
    )
    response_string = response.lower()
    try:
        metadata = {
            "title": response_string.split("title:")[1].split("2")[0].split("\n:")[0].strip(),
            "author": response_string.split("author:")[1].split("3")[0].split("\n")[0].strip(),
            "year": response_string.split("year:")[1].split("\n")[0].strip(),
        }
        return metadata
    except:
        return {"title": "error", "author": "error", "year": ""}