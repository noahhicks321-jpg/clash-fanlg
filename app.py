import streamlit as st
import pandas as pd
import random

# -------------------- INITIAL DATA --------------------
if "cards" not in st.session_state:
    st.session_state.cards = pd.DataFrame([
        {"Emoji": "⚔️", "Name": "Knight", "AtkDmg": 150, "AtkSpd": 1.2, "Range": 1.0, "HP": 800},
        {"Emoji": "🏹", "Name": "Archer", "AtkDmg": 120, "AtkSpd": 1.5, "Range": 5.0, "HP": 250},
        {"Emoji": "🐉", "Name": "Baby Dragon", "AtkDmg": 200, "AtkSpd": 1.8, "Range": 3.5, "HP": 1000},
        {"Emoji": "🧙", "Name": "Wizard", "AtkDmg": 250, "AtkSpd": 1.7, "Range": 5.5, "HP": 500},
        {"Emoji": "👹", "Name": "P.E.K.K.A", "AtkDmg": 600, "AtkSpd": 1.8, "Range": 1.0, "HP": 3000},
    ])
    st.session_state.cards["W"] = 0
    st.session_state.cards["L"] = 0
    st.session_state.cards["OVR"] = 0
    st.session_state.cards["Grade"] = "B"
    st.session_state.balance_history = []
    st.session_state.season_history = []
    st.session_state.retired = []

# -------------------- FUNCTIONS --------------------
def calculate_ovr(row):
    return round((row["AtkDmg"] * 0.4 + (1/row["AtkSpd"]) * 100 * 0.2 + row["Range"] * 20 * 0.1 + row["HP"] * 0.3)/10,1)

def assign_grade(ovr):
    if ovr >= 95: return "S+"
    elif ovr >= 90: return "S"
    elif ovr >= 85: return "A"
    elif ovr >= 80: return "B"
    else: return "C"

def simulate_season():
    cards = st.session_state.cards.copy()
    cards["W"] = 0
    cards["L"] = 0

    # 82 games per card (random matchups)
    for idx in range(len(cards)):
        for g in range(82):
            opponent = random.choice(cards.index[cards.index != idx])
            score_self = cards.loc[idx, "OVR"] + random.uniform(-5, 5)
            score_opp = cards.loc[opponent, "OVR"] + random.uniform(-5, 5)
            if score_self > score_opp:
                cards.loc[idx, "W"] += 1
                cards.loc[opponent, "L"] += 1
            else:
                cards.loc[idx, "L"] += 1
                cards.loc[opponent, "W"] += 1

    # Champion determination
    champion = cards.sort_values(["W","OVR"], ascending=False).iloc[0]
    st.session_state.season_history.append({"Season": len(st.session_state.season_history)+1, "Champion": champion["Name"], "Record": f"{champion['W']}-{champion['L']}", "OVR": champion["OVR"]})

    st.session_state.cards = cards

# -------------------- MAIN APP --------------------
st.title("Clash Royale – League Sim (Improved)")

# Recalculate OVR + Grades
st.session_state.cards["OVR"] = st.session_state.cards.apply(calculate_ovr, axis=1)
st.session_state.cards["Grade"] = st.session_state.cards["OVR"].apply(assign_grade)

# Tabs
main, balance, history, retired = st.tabs(["Card Stats", "Balance Changes", "History", "Retired Cards"])

with main:
    st.header("📊 Current Cards")

    # Dynamic grade color coding
    def color_grade(val):
        colors = {"S+":"#FFD700","S":"#FF8C00","A":"#4CAF50","B":"#2196F3","C":"#B0BEC5"}
        return f"background-color:{colors.get(val,'white')};color:black;font-weight:bold;"

    st.dataframe(st.session_state.cards.style.applymap(color_grade, subset=["Grade"]))

    if st.button("▶️ Simulate Season"):
        simulate_season()
        st.success("Season simulated! Check history tab for results.")

with balance:
    st.header("⚖️ Balance Changes")
    selected = st.selectbox("Select Card", st.session_state.cards["Name"])
    card_idx = st.session_state.cards[st.session_state.cards["Name"]==selected].index[0]

    dmg = st.number_input("Attack Damage", value=int(st.session_state.cards.loc[card_idx,"AtkDmg"]))
    spd = st.number_input("Attack Speed", value=float(st.session_state.cards.loc[card_idx,"AtkSpd"]), step=0.1)
    rng = st.number_input("Range", value=float(st.session_state.cards.loc[card_idx,"Range"]), step=0.1)
    hp = st.number_input("HP", value=int(st.session_state.cards.loc[card_idx,"HP"]))

    if st.button("Save Balance Change"):
        st.session_state.cards.loc[card_idx, ["AtkDmg","AtkSpd","Range","HP"]] = [dmg, spd, rng, hp]
        st.session_state.balance_history.append({"Card":selected,"AtkDmg":dmg,"AtkSpd":spd,"Range":rng,"HP":hp})
        st.success("Balance updated!")

    if st.button("Retire Card"):
        retired_card = st.session_state.cards.loc[card_idx]
        st.session_state.retired.append(retired_card)
        st.session_state.cards = st.session_state.cards.drop(card_idx)
        st.warning(f"{retired_card['Name']} retired!")

with history:
    st.header("📜 Balance Change History")
    if st.session_state.balance_history:
        st.table(pd.DataFrame(st.session_state.balance_history))
    else:
        st.info("No balance changes yet.")

    st.header("🏆 Season History")
    if st.session_state.season_history:
        st.table(pd.DataFrame(st.session_state.season_history))
    else:
        st.info("No seasons simulated yet.")

with retired:
    st.header("🚪 Retired Cards")
    if st.session_state.retired:
        st.table(pd.DataFrame(st.session_state.retired))
    else:
        st.info("No retired cards.")
