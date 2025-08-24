import streamlit as st
import pandas as pd
import random

# -------------------- INITIAL DATA --------------------
if "cards" not in st.session_state:
    # Start with 80 random cards instead of 5
    names = [f"Card {i+1}" for i in range(80)]
    emojis = ["⚔️","🏹","🐉","🧙","👹","🛡️","🔥","❄️","💀","⚡"]  # pool of emojis
    st.session_state.cards = pd.DataFrame([
        {
            "Emoji": random.choice(emojis),
            "Name": names[i],
            "AtkDmg": random.randint(100,600),
            "AtkSpd": round(random.uniform(1.0,2.0),1),
            "Range": round(random.uniform(1.0,6.0),1),
            "HP": random.randint(200,3000),
        }
        for i in range(80)
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
    raw = (row["AtkDmg"] * 0.4 + (1/row["AtkSpd"]) * 100 * 0.2 + row["Range"] * 20 * 0.1 + row["HP"] * 0.3) / 10
    # Clamp OVR between 60–99
    return max(60, min(99, round(raw, 1)))

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
    st.session_state.season_history.append({
        "Season": len(st.session_state.season_history)+1,
        "Champion": champion["Name"],
        "Record": f"{champion['W']}-{champion['L']}",
        "OVR": champion["OVR"]
    })

    st.session_state.cards = cards

# -------------------- MAIN APP --------------------
st.title("Clash Royale – League Sim (Restored Features)")

# Recalculate OVR + Grades
st.session_state.cards["OVR"] = st.session_state.cards.apply(calculate_ovr, axis=1)
st.session_state.cards["Grade"] = st.session_state.cards["OVR"].apply(assign_grade)

# Tabs
main, balance, history, retired, addcard = st.tabs(["Card Stats", "Balance Changes", "History", "Retired Cards", "Add Card"])

with main:
    st.header("📊 Current Standings")
    standings = st.session_state.cards.sort_values(["W","OVR"], ascending=False).reset_index(drop=True)

    def color_grade(val):
        colors = {"S+":"#FFD700","S":"#FF8C00","A":"#4CAF50","B":"#2196F3","C":"#B0BEC5"}
        return f"background-color:{colors.get(val,'white')};color:black;font-weight:bold;"

    st.dataframe(standings.style.applymap(color_grade, subset=["Grade"]))

    if st.button("▶️ Simulate Season"):
        simulate_season()
        st.success("Season simulated! Check history tab for results.")

with balance:
    st.header("⚖️ Balance Changes")

    # Show all cards in editable table (no dropdowns)
    edited = st.data_editor(
        st.session_state.cards[["Emoji","Name","AtkDmg","AtkSpd","Range","HP"]],
        num_rows="dynamic",
        key="balance_editor"
    )

    if st.button("Save All Changes"):
        st.session_state.cards.update(edited)
        for _, row in edited.iterrows():
            st.session_state.balance_history.append(row.to_dict())
        st.success("All balance changes saved!")

    if st.button("Retire First Card in List"):
        if not st.session_state.cards.empty:
            retired_card = st.session_state.cards.iloc[0]
            st.session_state.retired.append(retired_card)
            st.session_state.cards = st.session_state.cards.drop(st.session_state.cards.index[0])
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

with addcard:
    st.header("➕ Add New Card")
    emoji = st.text_input("Emoji", "⚔️")
    name = st.text_input("Name", f"Custom Card {len(st.session_state.cards)+1}")
    dmg = st.number_input("Attack Damage", min_value=50, max_value=1000, value=200)
    spd = st.number_input("Attack Speed", min_value=0.5, max_value=3.0, value=1.5, step=0.1)
    rng = st.number_input("Range", min_value=0.5, max_value=10.0, value=3.0, step=0.1)
    hp = st.number_input("HP", min_value=100, max_value=5000, value=800)

    if st.button("Add Card"):
        new_card = {"Emoji":emoji,"Name":name,"AtkDmg":dmg,"AtkSpd":spd,"Range":rng,"HP":hp,"W":0,"L":0,"OVR":0,"Grade":"C"}
        st.session_state.cards = pd.concat([st.session_state.cards, pd.DataFrame([new_card])], ignore_index=True)
        st.success(f"{name} added!")
