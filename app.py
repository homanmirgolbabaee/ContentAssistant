import streamlit as st
from PIL import Image
import assemblyai as aai
from pytube import YouTube
import os
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
import weaviate


# Configurations and Setups
aai.settings.api_key = os.environ.get('AASSEMBLY_API_KEY')
PAT = os.environ.get('PAT_KEY')
USER_ID = os.environ.get('USER_ID')
APP_ID = os.environ.get('APP_ID')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID')

# Initializing services
transcriber = aai.Transcriber()
channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.    V2Stub(channel)
metadata = (('authorization', 'Key ' + PAT),)
# Initiliazing weaviet 
auth_config = weaviate.AuthApiKey(api_key="RuOSJ44A4zNEIWLaoXr3M2cOLr95oUWx4nWy")
weaviate_client = weaviate.Client(
    url="https://my-sandbox-rpogjsdk.weaviate.network",
    auth_client_secret=auth_config
)
########################
#####################
# weaviet functions #
#####################
#########################

def save_mood_to_weaviate(mood, transcription):
    mood_data = {
        "mood": mood,
        "transcription": transcription
    }
    
    try:
        # Use the create method to add data
        weaviate_client.data_object.create(mood_data, "Mood")
    except Exception as e:
        st.error(f"Error saving mood and transcription to Weaviate: {e}")
    
    try:
        # Use the create method to add data
        weaviate_client.data_object.create(mood_data, "Mood")
    except Exception as e:
        st.error(f"Error saving mood to Weaviate: {e}")

def get_all_moods_and_transcriptions_from_weaviate():
    """Retrieve all moods and transcriptions from Weaviate."""
    # Fetching both mood and transcription properties
    query = weaviate_client.query.get("Mood", ["mood", "transcription"]).with_limit(100).do()
    if "data" in query and "Get" in query["data"] and "Mood" in query["data"]["Get"]:
        # Creating a list of dictionaries for each mood and transcription
        return [{"Mood": entry["mood"], "Transcription": entry["transcription"]} for entry in query["data"]["Get"]["Mood"]]
    return []

def transcribe_audio(file):
    """Transcribes an audio file."""
    temp_filename = "temp_file.ogg"
    with open(temp_filename, "wb") as f:
        f.write(file.getbuffer())
    transcript = transcriber.transcribe(temp_filename)
    os.remove(temp_filename)
    return transcript.text

def transcribe_youtube(url):
    """Transcribes audio from a YouTube URL."""
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    download_url = stream.url
    transcript = transcriber.transcribe(download_url)
    return transcript.text

def get_mood_clarifai(sentence):
    """Gets mood for a given sentence using Clarifai."""
    RAW_TEXT = 'Recognize the Mood of the following sentence: ' + sentence
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)
    post_workflow_results_response = stub.PostWorkflowResults(
        service_pb2.PostWorkflowResultsRequest(
            user_app_id=userDataObject,
            workflow_id=WORKFLOW_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        text=resources_pb2.Text(
                            raw=RAW_TEXT
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )

    if post_workflow_results_response.status.code != status_code_pb2.SUCCESS:
        print(post_workflow_results_response.status)
        raise Exception("Post workflow results failed, status: " + post_workflow_results_response.status.description)
    results = post_workflow_results_response.results[0]
    res = results.outputs[0].data.text.raw
    return res

def display_transcription_results(transcription, keyword):
    """Displays transcription and mood results in Streamlit."""
    st.text_area("Transcription:", transcription, height=250)
    # mood_clarifai = get_mood_clarifai(transcription)
    # st.write(f"Mood of the content (using Clarifai): **{mood_clarifai}**")
    if keyword:
        occurrences = transcription.lower().count(keyword.lower())
        st.write(f"'{keyword}' found {occurrences} times.")
        highlighted_text = transcription.replace(keyword, f'**{keyword}**')
        st.markdown(highlighted_text)
    st.download_button("Download Transcription", data=transcription, file_name="transcription.txt")

def set_page_background():
    """Sets the Streamlit page background using custom CSS."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1553095066-5014bc7b7f2d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8d2FsbCUyMGJhY2tncm91bmR8ZW58MHx8MHx8fDA%3D&w=1000&q=80");
            background-attachment: fixed;
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def display_sidebar():
    """
    Displays the sidebar options and returns the selected method.
    """
    user_type = st.sidebar.radio("", ["Standard User", "Content Creator (Soon!)", "Programmers (Soon!)"])
    
    if user_type == "Standard User":
        st.sidebar.header("Choose your method:")
        method = st.sidebar.radio("", ["Youtube/Upload", "Article Processing", "Observe Weaviate Database"])
        return method

    # Placeholder for future methods
    elif user_type == "Content Creator (Soon!)":
        st.sidebar.write("Stay tuned for exciting features!")
        return None

    elif user_type == "Programmers (Soon!)":
        st.sidebar.write("Exciting tools and features coming soon!")
        return None
    
def summarize_text_clarifai(text):
    """Gets Summarization for a given sentence using Clarifai."""
    RAW_TEXT = 'Summarize the following text under 100 words. the article : ' + text
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)
    post_workflow_results_response = stub.PostWorkflowResults(
        service_pb2.PostWorkflowResultsRequest(
            user_app_id=userDataObject,
            workflow_id=WORKFLOW_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        text=resources_pb2.Text(
                            raw=RAW_TEXT
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )

    if post_workflow_results_response.status.code != status_code_pb2.SUCCESS:
        print(post_workflow_results_response.status)
        raise Exception("Post workflow results failed, status: " + post_workflow_results_response.status.description)
    results = post_workflow_results_response.results[0]
    res = results.outputs[0].data.text.raw
    return res

def article_processing(user_text):
    """Processes an article to get its mood and summarize it."""
    with st.spinner("🔮 Detecting mood..."):
        mood = get_mood_clarifai(user_text)
    st.success(f"🎉 Predicted Mood using Clarifai: **{mood}**")

    # Add button to save mood to Weaviate
    if mood and st.button("Save Mood to Weaviate"):
        save_mood_to_weaviate(mood, user_text)
        st.success("Mood saved to Weaviate!")

    with st.spinner("📝 Summarizing text..."):
        summarized_text = summarize_text_clarifai(user_text)
    st.text_area("Summarized Transcript:", summarized_text, height=250)

def display_article_processing_results(text):
    """Handles the Article Processing method"""
    # Check if mood has already been detected
    if 'mood' not in st.session_state:
        mood = get_mood_clarifai(text)
        st.session_state.mood = mood
        st.success(f"🎉 Predicted Mood using Clarifai: **{mood}**")
    else:
        st.success(f"🎉 Predicted Mood using Clarifai: **{st.session_state.mood}**")
    
    # Check if summarize button is clicked
    if st.button("Summarize Text"):
        summarized_text = summarize_text_clarifai(text)
        st.text_area("Summarized Transcript:", summarized_text, height=250)

    # Option to save mood to Weaviate
    if st.session_state.mood and st.button("Save Mood to Weaviate"):
        save_mood_to_weaviate(st.session_state.mood, text)
        st.success("Mood saved to Weaviate!")


def main():
    
    set_page_background()
    
    col1, col2 = st.columns(2)
    with col2:  
        st.title("Pied Piper")
    
    st.sidebar.image("logo/logo.png", caption="Your App Logo")  # Logo in the sidebar
    method = display_sidebar()

    if method == "Youtube/Upload":
        yt_url = st.text_input("🎥 Enter the YouTube video URL (or skip to upload an audio file):")
        
        if yt_url:
            keyword = st.text_input("🔍 Find in transcription:")
            yt = YouTube(yt_url)
            st.image(yt.thumbnail_url, caption=yt.title, use_column_width=True)
            with st.spinner("🔄 Transcribing the YouTube video..."):
                transcription = transcribe_youtube(yt_url)
            display_transcription_results(transcription, keyword)
        
        else:
            uploaded_file = st.file_uploader("🎵 Upload an audio file:", type=["ogg", "mp3", "wav"])
            if uploaded_file:
                keyword = st.text_input("🔍 Find in transcription:")
                st.audio(uploaded_file, format='audio/ogg')
                if 'transcription' not in st.session_state:
                    with st.spinner("🔄 Transcribing your audio..."):
                        st.session_state.transcription = transcribe_audio(uploaded_file)
                display_transcription_results(st.session_state.transcription, keyword)
                
                
    #elif method == "Mood Recognition":
    #    user_sentence = st.text_area("📝 Enter the text to detect its mood:", height=150)
        # Initialize mood variable
    #    mood = None
    #    if user_sentence:
            # Check if mood already exists in session state
    #        if 'mood' in st.session_state:
    #            mood = st.session_state.mood
    #        else:
    #            with st.spinner("🔮 Detecting mood..."):
    #                mood = get_mood_clarifai(user_sentence)
    #                st.session_state.mood = mood  # Store the mood in session state
    #        st.success(f"🎉 Predicted Mood using Clarifai: **{mood}**")

            # Add button to save mood to Weaviate
    #        if mood and st.button("Save Mood to Weaviate"):
    #            save_mood_to_weaviate(mood, user_sentence)
    #            st.success("Mood saved to Weaviate!")
                
    elif method == "Observe Weaviate Database":
        with st.spinner("🔍 Fetching moods and transcriptions from Weaviate..."):
            moods_transcriptions = get_all_moods_and_transcriptions_from_weaviate()

        if moods_transcriptions:
            st.table(moods_transcriptions)  # Streamlit table display
        else:
            st.write("No moods and transcriptions found in the database.")
            
    #elif method == "Text Summarization":
        #user_text = st.text_area("📝 Enter the text to be summarized:", height=150)
        #if user_text:
    #        with st.spinner("📝 Summarizing text..."):
    #            summarized_text = summarize_text_clarifai(user_text)
    #        st.text_area("Summarized Transcript:", summarized_text, height=250)    
    elif method == "Article Processing":
        user_text = st.text_area("📝 Enter the text for mood detection and summarization:", height=150)
        if user_text:
            display_article_processing_results(user_text)      
if __name__ == "__main__":
    main()
