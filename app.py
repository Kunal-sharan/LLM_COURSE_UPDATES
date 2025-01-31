import pandas as pd
import requests
from datetime import datetime, timedelta
import streamlit as st
import plotly.express as px
from groq import Groq
st.set_page_config(layout="wide")


client = Groq(
    api_key=st.secrets["GROQ_API_KEY"],
)
def get_summary(txt):
   
  chat_completion = client.chat.completions.create(
      messages=[
          {
              "role": "user",
              "content":f"Using This {txt} \n generate a simple , concise summary whithout adding anything extra just provide a simple and complete summary keep the tone first person if you can not generate a summary return the original text"
          }
      ],
      model="llama-3.3-70b-versatile",
      stream=False,
  )

  return chat_completion.choices[0].message.content

@st.fragment
def carousel(map):
    text_items=[]
    names = []
    for i in map:
        text_items.append(map[i])
        names.append(i)

    # Streamlit app layout
    st.title("🔄 Students learning")

      
    if 'index' not in st.session_state:
        st.session_state.index = 0

    # Display the current text item
    with st.container(border=True,height=300):
        st.header(names[st.session_state.index])
        st.markdown(f"{text_items[st.session_state.index]}")

    col1, col2 = st.columns([7,1])
    
    with col1:
        if st.button("Previous"):
            st.session_state.index = (st.session_state.index - 1) % len(text_items)
    
    with col2:
        if st.button("Next"):
            st.session_state.index = (st.session_state.index + 1) % len(text_items)

def get_time_difference(start_time, end_time):
    # Define the format
    time_format = "%I:%M:%S %p"

    # Convert strings to datetime objects
    start_dt = datetime.strptime(start_time, time_format)
    end_dt = datetime.strptime(end_time, time_format)

    # If end time is earlier in the day than start time, assume it is on the next day
    if end_dt < start_dt:
        end_dt += timedelta(days=1)

    # Calculate the difference
    time_difference = end_dt - start_dt

    # Print the result
    return str(time_difference)


def add_time_durations(durations):
    total_duration = timedelta()

    for duration in durations:
        h, m, s = map(int, duration.split(":"))
        total_duration += timedelta(hours=h, minutes=m, seconds=s)

    # Extract total hours, minutes, and seconds
    total_seconds = int(total_duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format output as HH:MM:SS
    return f"{hours:02}:{minutes:02}:{seconds:02}"

YOUR_SHEET_ID='15iywUXaAfWWbv4Bc7ipV_0myV2WvYZ6HBH4gOiQNFO0'

with requests.get(f'https://docs.google.com/spreadsheet/ccc?key={YOUR_SHEET_ID}&output=csv') as r:
  open('dataset.csv', 'wb').write(r.content)
  df = pd.read_csv('dataset.csv')
all_roll=set(df['Roll Number'])

total_duration_map={}
for i in all_roll:
  selected_rows = df[df['Roll Number']==i]
  total_duration_map[i]=total_duration_map.get(i,None)
  arr = []
  for j in range(len(selected_rows)):
    start_time=selected_rows.iloc[j]['What was your approximate start time of study today?']
    end_time=selected_rows.iloc[j]['What was your approximate  of time of LLM studies today? You are expected to study for 1 hour minimum']
    arr.append(get_time_difference(start_time, end_time))
  total_duration_map[i]=add_time_durations(arr)



final_arr=[]
all_learnings={}
for i in all_roll:
  s_rows = df[df["Roll Number"]==i]
  learnings = ""
  for j in range(len(s_rows)):
    learnings+= str(s_rows.iloc[j]['Timestamp'])+" :" +str(s_rows.iloc[j]['Summarise your days learing on the topics.'])+"\n"
  summ_learnings = learnings 
  k = df[df['Roll Number']==i].iloc[0]['Name']+f"({i})"
  all_learnings[k] = all_learnings.get(k,"")+summ_learnings
# all_learnings    

for i in total_duration_map:
  final_arr.append({
      "Roll Number":i,
      "Name":df[df['Roll Number']==i].iloc[0]['Name'],
      "Total Duration(hrs:min:sec)":total_duration_map[i]
  })
# Convert Time Duration to proper time format
df = pd.DataFrame(final_arr)
df["Time Delta"] = pd.to_timedelta(df["Total Duration(hrs:min:sec)"]).dt.total_seconds()  # Convert to seconds

# Streamlit UI

st.title("LLM course duration analysis")
if st.button("Show latest data"):
  with st.spinner("Analyzing.."):  
# Sort original DataFrame by Time Duration (but keep the original format)
    sorted_df = df.sort_values(by="Time Delta",ascending=False).drop(columns=["Time Delta"])

    # Display Sorted DataFrame
    st.write("### Leaderboard (Sorted by Time Duration)")
    st.dataframe(sorted_df,width=1200,hide_index=False)

    # Create a Bar Chart for Time Duration
    fig = px.bar(df, x="Name", y="Time Delta", text="Total Duration(hrs:min:sec)",
                labels={"Time Delta": "Time (seconds)"},
                title="Time Duration of Participants",
                color="Time Delta", color_continuous_scale="Blues")
    st.plotly_chart(fig)

    # Show Leaderboard Chart on Button Click
    fig_leaderboard = px.bar(df.sort_values(by="Time Delta"), x="Name", y="Time Delta", 
                            text="Total Duration(hrs:min:sec)",
                            labels={"Time Delta": "Time (seconds)"},
                            title="Leaderboard Ranking",
                            color="Time Delta", color_continuous_scale="Greens")
    st.plotly_chart(fig_leaderboard)
    # df["Total Duration(hrs:min:sec)"] = pd.to_timedelta(df["Total Duration(hrs:min:sec)"])
    carousel(all_learnings)
# put carousel here
    
