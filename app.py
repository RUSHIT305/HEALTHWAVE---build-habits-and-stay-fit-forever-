import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io, time, base64, os, datetime, random
import plotly.express as px

st.set_page_config(page_title='HealthWave', layout='wide', page_icon='🌊')

# --- Utilities ---
def init_state():
    if 'logs' not in st.session_state:
        st.session_state['logs'] = []  # each entry: dict with date, exercise, duration, water, sleep, mood, calories, weight
    if 'tips' not in st.session_state:
        st.session_state['tips'] = [
            'Drink a glass of water first thing in the morning. 💧',
            'Stand up and stretch every hour to improve circulation. 🧘',
            'Aim for 7–9 hours of sleep for better recovery. 🛌',
            'Short high-intensity bursts (1–2 min) can boost metabolism. 🏃‍♂️',
            'Practice box breathing: 4s inhale - 4s hold - 4s exhale - 4s hold. 🫁'
        ]
    if 'selected_date' not in st.session_state:
        st.session_state['selected_date'] = datetime.date.today()

def save_log(entry):
    st.session_state['logs'].append(entry)

def logs_df():
    if len(st.session_state['logs'])==0:
        return pd.DataFrame(columns=['date','exercise','duration_min','water_glasses','sleep_h','mood','calories','weight_kg'])
    return pd.DataFrame(st.session_state['logs'])

def csv_download_link(df, filename='health_logs.csv'):
    towrite = io.BytesIO()
    df.to_csv(towrite, index=False)
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'
    return href

init_state()

# --- Sidebar ---
st.sidebar.title('HealthWave')
st.sidebar.markdown('A polished wellness tracker')
page = st.sidebar.radio('Navigate', ['Dashboard','Daily Tracker','Insights','Wellness','Data'])

st.sidebar.divider = lambda: st.sidebar.markdown('---')
st.sidebar.divider()

st.sidebar.subheader('Quick Log')
with st.sidebar.form('quick_log', clear_on_submit=True):
    q_ex = st.text_input('Exercise (quick)', placeholder='e.g., Jogging')
    q_dur = st.number_input('Duration (min)', min_value=0, max_value=600, value=20)
    q_water = st.number_input('Water (glasses)', min_value=0, max_value=20, value=2)
    submitted = st.form_submit_button('Add Quick Log')
    if submitted:
        entry = {
            'date': str(datetime.date.today()),
            'exercise': q_ex or '—',
            'duration_min': int(q_dur),
            'water_glasses': int(q_water),
            'sleep_h': None,
            'mood': None,
            'calories': None,
            'weight_kg': None
        }
        save_log(entry)
        st.sidebar.success('Saved ✅')

st.sidebar.divider()
st.sidebar.markdown('**Tip of the day**')
st.sidebar.info(random.choice(st.session_state['tips']))

# --- Pages ---
if page == 'Dashboard':
    st.title('🌊 HealthWave — Dashboard')
    st.markdown('Overview of today and quick actions.')

    today = st.session_state['selected_date'] = st.date_input('Select date', value=st.session_state['selected_date'])

    df = logs_df()
    today_str = str(today)
    todays = df[df['date']==today_str] if not df.empty else pd.DataFrame()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric('Water (glasses)', int(todays['water_glasses'].sum()) if not todays.empty else 0)
    with c2:
        st.metric('Exercise (min)', int(todays['duration_min'].sum()) if not todays.empty else 0)
    with c3:
        sl = todays['sleep_h'].dropna()
        st.metric('Sleep (h)', round(float(sl.iloc[-1]) if not sl.empty else 0,1))
    with c4:
        m = todays['mood'].dropna()
        st.metric('Mood', m.iloc[-1] if not m.empty else '—')

    st.markdown('### Recent entries')
    if todays.empty:
        st.info('No entries for selected date. Add one in **Daily Tracker**.')
    else:
        st.table(todays.sort_values('date', ascending=False).reset_index(drop=True))

elif page == 'Daily Tracker':
    st.title('📝 Daily Tracker')
    st.markdown('Log your day—exercise, water, sleep, mood and weight. Data is stored in the app session.')

    with st.form('entry_form'):
        date = st.date_input('Date', value=datetime.date.today())
        exercise = st.text_input('Exercise (name)', placeholder='Push-ups, Jogging, Yoga...')
        duration = st.number_input('Duration (minutes)', min_value=0, max_value=600, value=30)
        water = st.number_input('Water (glasses)', min_value=0, max_value=50, value=8)
        sleep = st.number_input('Sleep (hours)', min_value=0.0, max_value=24.0, value=7.0, step=0.5)
        mood = st.selectbox('Mood', ['Very Bad','Bad','Neutral','Good','Very Good'], index=3)
        calories = st.number_input('Calories consumed (approx)', min_value=0, max_value=10000, value=2000)
        weight = st.number_input('Weight (kg)', min_value=20.0, max_value=300.0, value=70.0, step=0.1)
        save = st.form_submit_button('Save entry')

        if save:
            entry = {
                'date': str(date),
                'exercise': exercise or '—',
                'duration_min': int(duration),
                'water_glasses': int(water),
                'sleep_h': float(sleep),
                'mood': mood,
                'calories': int(calories),
                'weight_kg': float(weight)
            }
            save_log(entry)
            st.success('Entry saved ✅')

    st.markdown('---')
    st.markdown('#### Quick view — last 7 entries')
    df = logs_df()
    if df.empty:
        st.info('No logs yet — add your first entry above.')
    else:
        st.table(df.tail(7).sort_values('date', ascending=False).reset_index(drop=True))

elif page == 'Insights':
    st.title('📈 Progress & Insights')
    st.markdown('Visualize trends — weight, water, sleep and activity.')

    df = logs_df()
    if df.empty:
        st.info('No data yet — add entries in the Daily Tracker.')
    else:
        # Ensure correct types
        df['date'] = pd.to_datetime(df['date'])
        df_sorted = df.sort_values('date')
        # Weight trend
        if df_sorted['weight_kg'].notna().any():
            st.subheader('Weight Trend')
            fig = px.line(df_sorted, x='date', y='weight_kg', markers=True)
            st.plotly_chart(fig, use_container_width=True)
        # Water
        if df_sorted['water_glasses'].notna().any():
            st.subheader('Water Intake (last entries)')
            fig2 = px.bar(df_sorted, x='date', y='water_glasses')
            st.plotly_chart(fig2, use_container_width=True)
        # Sleep
        if df_sorted['sleep_h'].notna().any():
            st.subheader('Sleep (hours)')
            fig3 = px.line(df_sorted, x='date', y='sleep_h', markers=True)
            st.plotly_chart(fig3, use_container_width=True)

        # Activity summary
        st.subheader('Activity distribution')
        act = df_sorted.groupby('exercise').duration_min.sum().reset_index().sort_values('duration_min', ascending=False)
        if not act.empty:
            fig4 = px.pie(act, names='exercise', values='duration_min')
            st.plotly_chart(fig4, use_container_width=True)

elif page == 'Wellness':
    st.title('🧘 Wellness & Mindfulness')
    st.markdown('Short exercises and wellbeing tips to reset your mind.')

    col1, col2 = st.columns([2,1])
    with col1:
        st.subheader('Guided Breathing — Box Breathing')
        st.markdown('Follow the on-screen timer: Inhale 4s → Hold 4s → Exhale 4s → Hold 4s (repeat)')
        if st.button('Start 1 minute breathing'):
            placeholder = st.empty()
            total = 60
            for i in range(total, 0, -1):
                phase = (60 - i) % 16
                if phase < 4:
                    instruction = f'Inhale — {4 - (phase)}s'
                elif phase < 8:
                    instruction = f'Hold — {8 - (phase)}s'
                elif phase < 12:
                    instruction = f'Exhale — {12 - (phase)}s'
                else:
                    instruction = f'Hold — {16 - (phase)}s'
                placeholder.markdown(f'### {instruction}  —  Remaining {i}s')
                time.sleep(1)
            placeholder.markdown('### Finished — well done! 🎉')
    with col2:
        st.subheader('Daily Tip')
        st.info(random.choice(st.session_state['tips']))
        st.markdown('---')
        st.subheader('Quick Actions')
        if st.button('Add hydration +1 glass'):
            today = str(datetime.date.today())
            entry = {'date': today, 'exercise':'—', 'duration_min':0, 'water_glasses':1, 'sleep_h':None, 'mood':None, 'calories':None, 'weight_kg':None}
            save_log(entry)
            st.success('Added +1 glass ✅')

elif page == 'Data':
    st.title('💾 Data — Export / Import')
    df = logs_df()
    st.markdown('You can export your logs to CSV or import CSV (same format) to load history.')
    if df.empty:
        st.info('No data to export yet.')
    else:
        st.markdown(csv_download_link(df), unsafe_allow_html=True)
        st.download_button('Download CSV', df.to_csv(index=False).encode('utf-8'), 'health_logs.csv', 'text/csv')

    st.markdown('---')
    st.subheader('Import CSV')
    uploaded = st.file_uploader('Upload CSV', type=['csv'])
    if uploaded:
        try:
            newdf = pd.read_csv(uploaded)
            # validate minimal columns
            needed = {'date','exercise','duration_min','water_glasses','sleep_h','mood','calories','weight_kg'}
            if needed.issubset(set(newdf.columns)):
                # convert rows to dicts and extend
                for _, r in newdf.iterrows():
                    st.session_state['logs'].append({
                        'date': str(r['date']),
                        'exercise': r['exercise'],
                        'duration_min': int(r['duration_min']) if not pd.isna(r['duration_min']) else 0,
                        'water_glasses': int(r['water_glasses']) if not pd.isna(r['water_glasses']) else 0,
                        'sleep_h': float(r['sleep_h']) if not pd.isna(r['sleep_h']) else None,
                        'mood': r['mood'] if not pd.isna(r['mood']) else None,
                        'calories': int(r['calories']) if not pd.isna(r['calories']) else None,
                        'weight_kg': float(r['weight_kg']) if not pd.isna(r['weight_kg']) else None
                    })
                st.success('Imported CSV ✅')
            else:
                st.error('CSV missing required columns. See README for format.')
        except Exception as e:
            st.error(f'Failed to import CSV: {e}')

# Footer
st.markdown('---')
st.caption('HealthWave — built with ❤️ for HackVortex Codestorm 5. Store is session-only; for persistence use a database.')
