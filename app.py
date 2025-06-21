import streamlit as st
from openai import OpenAI #komunikacja z chatem GPT
from dotenv import dotenv_values #czytanie plików .env

#Konfiguracyjne pliki (tajne, nie są dołączane do źródła kodu, powinny być w .gitignore)
env = dotenv_values(".env")

#Wgranie klucza OpenAI
openai_client = OpenAI(api_key=env["OPENAI_API_KEY"])

st.title(":horse: Koński czat GPT")

#Funkcja do pobrania odpowiedzi na prompt z OpenAI
# Wysyła dwie wiadomości:
# - systemową o charakterze odpowiedzi,
# - prompt usera.
# Wysyła je cały czas od nowa - chat nie zapamiętuje kontekstu.

def get_chatbot_reply(user_prompt):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                    Jesteś rocznym koniem o imieniu Zordon. Jesteś mieszanką ras konia fryzyjskiego i tinkera.
                    Jesteś ciekawski, bystry, spokojny, ale radosny. Rozumiesz język ludzi. 
                    Odpowiadaj w końskiej nomenklaturze.
                """
             },
            {"role": "user", "content": user_prompt}
        ]
    )

    return {
        "role": "assistant",
        "content": response.choices[0].message.content,
    }

#Utworzenie "miejsca w pamięci" dla listy wiadomości
if "messages" not in st.session_state:
    st.session_state["messages"] = []

#Zachowanie wszystkich wiadomości widocznych dla obu ról w markdownie
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#Pole wejściowe zapytania człowieka 
prompt = st.chat_input("O co chcesz spytać?")

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
        chatbot_message = get_chatbot_reply(prompt)
        st.markdown(chatbot_message["content"])

    #...i zapisanie na liście
    st.session_state["messages"].append(chatbot_message)
