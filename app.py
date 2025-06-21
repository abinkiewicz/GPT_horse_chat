import streamlit as st


st.title(":parrot: Papuga!")

#Jeżeli klucza "messages" nie ma w pamięci to go dodaj w formie listy
if "messages" not in st.session_state:
    st.session_state["messages"] = []

#Wyświetlenie wszystkich wiadomości od człowieka i AI zapisanych poniżej przy pomocy append
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#Miejsce, gdzie wpisujemy prompt z zapytaniem do chata
prompt = st.chat_input("O co chcesz spytać?")
if prompt:
    #Wewnątrz chat message dodaj markdowna z promptem od użytkownika, z emotką buzi
    with st.chat_message("human"):
        st.markdown(prompt)

    #Zapisanie wiadomości człowieka w pamięci tak, aby nie zniknęła po odświeżeniu
    st.session_state["messages"].append({
        "role": "human", 
        "content": prompt}
        )

    #Wyświetlenie odpowiedzi AI
    with st.chat_message("ai"):
        response = f"Powtarzam! {prompt}"
        st.markdown(response)

    #Zapisanie wiadomości AI w pamięci tak, aby nie zniknęła po odświeżeniu
    st.session_state["messages"].append({
        "role": "ai", 
        "content": response}
        )
