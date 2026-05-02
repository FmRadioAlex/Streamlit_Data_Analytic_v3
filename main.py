import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client



supabase_config = st.secrets["supabase"]

SUPABASE_URL = supabase_config["url"]
SUPABASE_KEY = supabase_config["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_data():
    res = supabase.table("data").select("*").execute()
    df = pd.DataFrame(res.data)

    if df.empty:
        df = pd.DataFrame(columns=["date", "nick", "silver", "given"])

    return df

def add_row(date, nick, silver):
    supabase.table("data").insert({
        "date": date,
        "nick": nick,
        "silver": silver,
        "given": False
    }).execute()

def mark_given(nick):
    supabase.table("data").update({"given": True}).eq("nick", nick).execute()

def delete_row(row_id):
    supabase.table("data").delete().eq("id", row_id).execute()

def log_action(user, action, nick="", silver=None):
    supabase.table("logs").insert({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "nick": nick,
        "silver": silver
    }).execute()

st.set_page_config(page_title="Silver Manager", page_icon="💰")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

if not st.session_state.authenticated:
    nick = st.text_input("Name:")
    pwd = st.text_input("Пароль:", type="password")

    if st.button("Увійти"):
        users = st.secrets["database"]["users"]

        if nick in users and pwd == users[nick]:
            st.session_state.authenticated = True
            st.session_state.user = nick
            log_action(nick, "Login")
            st.rerun()
        else:
            st.error("❌ Wrong login")

    st.stop()

df = load_data()

tabs = st.tabs(["💰 Головна", "📊 Статистика", "🧾 Логи"])

with tabs[0]:
    st.write("User:", st.session_state.user)

    with st.sidebar:
        st.subheader("➕ Додати запис")
        with st.form("add_form"):
            nick = st.text_input("Нік")
            silver = st.number_input("Срібло", min_value=0)
            date = st.date_input("Дата")

            if st.form_submit_button("Добавити"):
                add_row(date.strftime("%Y-%m-%d"), nick, silver)
                log_action(st.session_state.user, "Add", nick, silver)
                st.rerun()

        not_given = df[df["given"] == False]

        if not not_given.empty:
            selected = st.selectbox("Select", not_given["nick"].unique())
            
            st.write(f"Total to give: **{int(not_given[not_given['nick'] == selected]['silver'].sum()):,} silver**")
            if st.button("Mark as given"):
                mark_given(selected)
                log_action(st.session_state.user, "Given", selected)
                st.rerun()

    st.dataframe(df,hide_index=False)

    st.subheader("🗑️ Видалити строчку")
    if not df.empty:
        df['Label'] = df.apply(lambda row: f"{row['date']} - {row['nick']} - {row['silver']} silver", axis=1)
        row_to_delete = st.selectbox("Select row to delete", df["Label"])
        if st.button("Delete"):
            row_id = df[df["Label"] == row_to_delete]["id"].values[0]
            delete_row(row_id)
            log_action(st.session_state.user, "Delete", row_to_delete)
            st.rerun()
    # if not df.empty:
    #     selected_id = st.selectbox("Delete row", df["id"])
    #     if st.button("Delete"):
    #         delete_row(selected_id)
    #         log_action(st.session_state.user, "Delete")
    #         st.rerun()

with tabs[1]:
    if not df.empty:
        col1, col2 = st.columns(2)
        # col1.metric("Total", f"{int(df['silver'].sum()):,}")
        # col2.metric("Given", f"{int(df[df['given'] == True]['silver'].sum()):,} ")
        # col3.metric("Not Given", f"{int(df[df['given'] == False]['silver'].sum()):,} ")
        col1.metric("Total Silver", f"{int(df['silver'].sum()):,}")
        
        col2.image(r"https://media1.tenor.com/m/Y5CKgQyhMb8AAAAC/crying-dog-watery-eyes.gif")
        st.audio("Dominic_Fike_-_Babydoll_(SkySound.cc).mp3")
        
        st.metric("Given Silver", f"{int(df[df['given'] == True]['silver'].sum()):,}")
        st.metric("Not Given Silver", f"{int(df[df['given'] == False]['silver'].sum()):,}")
        st.bar_chart(df.groupby("nick")["silver"].sum())

with tabs[2]:
    logs = supabase.table("logs").select("*").execute()
    logs_df = pd.DataFrame(logs.data)

    if not logs_df.empty:
        st.dataframe(logs_df.sort_values("time", ascending=False))