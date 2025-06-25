import streamlit as st
from openai import OpenAI #komunikacja z chatem GPT
from dotenv import dotenv_values #czytanie plików .env
import json
from pathlib import Path

#Słownik słowników o cenach
model_pricings = {
    "gpt-4o": {
        "input_tokens": 5.00 / 1_000_000,  # per token + rozdzielanie zer _
        "output_tokens": 15.00 / 1_000_000,  # per token
    },
    "gpt-4o-mini": {
        "input_tokens": 0.150 / 1_000_000,  # per token
        "output_tokens": 0.600 / 1_000_000,  # per token
    }
}

MODEL = "gpt-4o"
USD_TO_PLN = 50
PRICING = model_pricings[MODEL]

#Konfiguracyjne pliki (tajne, nie są dołączane do źródła kodu, powinny być w .gitignore)
env = dotenv_values(".env")

#Wgranie klucza OpenAI
openai_client = OpenAI(api_key=env["OPENAI_API_KEY"])


#
# Chatbot
#

#Funkcja do pobrania odpowiedzi na prompt z OpenAI
# Wysyła dwie wiadomości:
# - systemową o charakterze odpowiedzi,
# - prompt usera.

def get_chatbot_reply(user_prompt, memory):
    #Messages: Dodaj system message o roli
    messages = [
        {
            "role": "system",
            "content": st.session_state["chatbot_personality"]
        },
    ]
    #Messages: Dodaj ostatnie wiadomości z pamięci
    for message in memory:
        messages.append(
            {"role": message["role"], 
             "content": message["content"]}
             )

    #Messages: Prześlij najnowszą wiadomość użytkownika
    messages.append(
        {"role": "user", 
         "content": user_prompt}
         )

    #Poproś o odpowiedź i użyj modelu gpt-4o
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=messages
    )
    #Informacja o tym, ile tokenów (~sylab) generuje ta wiadomość
    usage = {}
    if response.usage:
        #Słownik usage z tokenami
        usage = {
            #WE i WY inaczej wyceniane
            #wejście
            "completion_tokens": response.usage.completion_tokens,
            #wyjście
            "prompt_tokens": response.usage.prompt_tokens,
            #razem
            "total_tokens": response.usage.total_tokens,
        }

    #Odpowiedź zwrotna
    return {
        "role": "assistant",
        "content": response.choices[0].message.content,
        "usage": usage,
    }

#
# Historia konwersacji i baza danych
#
DEFAULT_PERSONALITY = """
Jesteś pomocnikiem, który odpowiada na wszystkie pytania użytkownika.
Odpowiadaj na pytania w sposób zwięzły i zrozumiały.
""".strip()

DB_PATH = Path("db")
DB_CONVERSATIONS_PATH = DB_PATH / "conversations"
# db/
# ├── current.json
# ├── conversations/
# │   ├── 1.json
# │   ├── 2.json
# │   └── ...
# Funkcja łącząca wszystkie potrzebne dane z session_state
def load_conversation_to_state(conversation):
    st.session_state["id"] = conversation["id"]
    st.session_state["name"] = conversation["name"]
    st.session_state["messages"] = conversation["messages"]
    st.session_state["chatbot_personality"] = conversation["chatbot_personality"]

# Ładowanie aktualnej konwersacji lub tworzenie nowej, jeżeli jej nie było
def load_current_conversation():
    if not DB_PATH.exists():
        DB_PATH.mkdir()
        DB_CONVERSATIONS_PATH.mkdir()
        conversation_id = 1
        conversation = {
            "id": conversation_id,
            "name": "Konwersacja 1",
            "chatbot_personality": DEFAULT_PERSONALITY,
            "messages": [],
        }

        # tworzymy nową konwersację
        with open(DB_CONVERSATIONS_PATH / f"{conversation_id}.json", "w") as f:
            f.write(json.dumps(conversation))

        # która od razu staje się aktualną
        with open(DB_PATH / "current.json", "w") as f:
            f.write(json.dumps({
                "current_conversation_id": conversation_id,
            }))

    else:
        # sprawdzamy, która konwersacja jest aktualna
        with open(DB_PATH / "current.json", "r") as f:
            data = json.loads(f.read())
            conversation_id = data["current_conversation_id"]

        # wczytujemy konwersację
        with open(DB_CONVERSATIONS_PATH / f"{conversation_id}.json", "r") as f:
            conversation = json.loads(f.read())

# Wywołanie funkcji łączącej dane z session_statem
    load_conversation_to_state(conversation)

#
# Main
#

load_current_conversation()
st.title(":horse: GPT horse chat")

#Utworzenie "miejsca w pamięci" dla listy wiadomości
if "messages" not in st.session_state:
    if Path("current_conversation.json").exists():
        with open("current_conversation.json", "r") as f:
            chatbot_conversation = json.load(f)

        st.session_state["messages"] = chatbot_conversation["messages"]
        st.session_state["chatbot_personality"] = chatbot_conversation["chatbot_personality"]

    else:
        st.session_state["messages"] = []

#Zachowanie wszystkich wiadomości widocznych dla obu ról w markdownie
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#Pole wejściowe zapytania człowieka 
prompt = st.chat_input("Ask me anything")

#Po pojawieniu się promptu człowieka...
if prompt:
    user_message = {"role": "user", "content": prompt}
    #...odczytaj i wyświetl go...
    with st.chat_message("user"):
        st.markdown(user_message["content"])

    #...i zapisz
    st.session_state["messages"].append(user_message)

    #Pobranie odpowiedzi od bota...
    with st.chat_message("assistant"):
        chatbot_message = get_chatbot_reply(
            prompt,
            memory=st.session_state['messages'][-10:] #Pobranie 10 najnowszych wiadomości
            )
        st.markdown(chatbot_message["content"])

    #...i zapisanie na liście
    st.session_state["messages"].append(chatbot_message)

    #Zapis wiadomości w pliku
    with open("current_conversation.json", "w") as f:
        f.write(json.dumps({
            "chatbot_personality": st.session_state["chatbot_personality"],
            "messages": st.session_state["messages"],
        }))

#Pasek boczny historii rozmowy
with st.sidebar:
    st.write("Current model", MODEL)

    total_cost = 0
    for message in st.session_state["messages"]:
        if "usage" in message:
            total_cost += message["usage"]["prompt_tokens"] * PRICING["input_tokens"]
            total_cost += message["usage"]["completion_tokens"] * PRICING["output_tokens"]

    c0, c1 = st.columns(2)
    with c0:
        st.metric("Chat cost (USD)", f"${total_cost:.4f}")

    with c1:
        st.metric("Chat cost (PLN)", f"{total_cost * USD_TO_PLN:.4f}")

    #Osobowość chata wprowadzana z pola w app (text_area)
    st.session_state["chatbot_personality"] = st.text_area(
        "Describe chatbot personality",
        max_chars=1000,
        height=200,
        value="""
You are a yearling horse named Zordon. You are a mix of breeds of Friesian horse and tinker.
You are inquisitive, smart, calm but cheerful. You understand the language of people. 
Respond in horse nomenclature.
        """.strip()
    )
