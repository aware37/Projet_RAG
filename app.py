import streamlit as st


def main():
    st.set_page_config(
        page_title="RAG Application",
        page_icon=":robot_face:",
        layout="wide",
        initial_sidebar_state="auto"
    )

    st.header("Welcome to the RAG Application :robot_face:")
    st.text_input("Ask a question and get answers based on the subject of Retrieval-Augmented Generation (RAG).")

    with st.sidebar:
        st.subheader("About")
        st.write("This application uses RAG to provide answers based on retrieved documents already implemented.")
        st.write("Developed by the NLP Project Team.")

if __name__ == "__main__":
    main()  