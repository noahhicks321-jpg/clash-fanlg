import streamlit as st
import pandas as pd
import random

# -------------------- INITIAL DATA --------------------
CARD_POOL = [
    "Knight","Archer","Baby Dragon","Wizard","P.E.K.K.A","Giant","Mini P.E.K.K.A","Hog Rider","Valkyrie","Musketeer",
    "Bomber","Skeleton Army","Prince","Dark Prince","Spear Goblins","Goblin Barrel","Witch","Ice Wizard","Electro Wizard","Mega Minion",
    "Hunter","Royal Giant","Cannon Cart","Flying Machine","Magic Archer","Inferno Dragon","Miner","Lumberjack","Bandit","Battle Ram",
    "Ram Rider","Mega Knight","Archers","Firecracker","Zappies","Rascals","Royal Hogs","Elite Barbarians","Ice Spirit","Electro Spirit",
    "Goblin Gang","Guards","Barbarians","Wall Breakers","Bats","Skeletons","Graveyard","X-Bow","Mortar","Cannon",
    "Tesla","Bomb Tower","Inferno Tower","Goblin Hut","Barbarian Hut","Furnace","Elixir Collector","Tombstone","Goblin Cage","Battle Healer",
    "Mother Witch","Phoenix","Monk","Skeleton King","Archer Queen","Golden Knight","Fisherman","Dart Goblin","Royal Ghost","Three Musketeers",
    "Ice Golem","Goblin Drill","Sparky","Balloon","Rocket","Lightning","Fireball","Zap","Arrows","Log"
]

if "cards" not in st.session_state:
    chosen = random.sample(CARD_POOL, 80)
    emojis = ["⚔️","🏹","🐉","🧙","👹","🛡️","🔥","❄️","💀","⚡"]
    st.session_state.cards = pd.DataFrame([
        {
            "Emoji": random.choice(emojis),
            "Name": chosen[i],
            "AtkDmg": random.randint(150,500),
            "AtkSpd": round(random.uniform(1.0,2.0),1),
            "Range": round(random.uniform(1.0,6.0),1),
            "HP": random.randint(500,2500),
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
    st.session_state.card_history = {}
    st.session_state.standings_snapshots = {}  # save standings at end of each season

# -------------------- FUNCTIONS --------------------
def calculate_ovr(row):
    raw = (row["AtkDmg"] * 0.4 + (1/row["AtkSpd"]) * 100 * 0.2 +
           row["Range"] * 20 * 0.1 + row["HP"] * 0.3) / 10
    return max(60, min(99, round(raw, 1)))

def assign_grade(ovr):
    if ovr >= 95: return "S+"
    elif ovr >= 90: return "S"
    elif ovr >= 85: return "A"
    elif ovr >= 80: return "B"
    else: return "C"

def simulate_season():
    cards = st.session_state.cards.copy()
    cards["W"], cards["L"] = 0, 0
    season_num = len(st.session_state.season_history)+1

    # Each card plays 82 games with weighted outcome
    for idx in range(len(cards)):
        opponents = random.choices(cards.index[cards.index != idx], k=82)
        for opp in opponents:
            score_self = cards.loc[idx,"OVR"]*0.78 + random.uniform(-5,5)*0.22
            score_opp = cards.loc[opp,"OVR"]*0.78 + random.uniform(-5,5)*0.22
            if score_self > score_opp:
                cards.loc[idx,"W"] += 1
                cards.loc[opp,"L"] += 1
            else:
                cards.loc[idx,"L"] += 1
                cards.loc[opp,"W"] += 1

    champion = cards.sort_values(["W","OVR"], ascending=False).iloc[0]
    st.session_state.season_history.append({
        "Season": season_num,
        "Champion": champion["Name"],
        "Record": f"{champion['W']}-{champion['L']}",
        "OVR": champion["OVR"]
    })

    # Save per-card season history
    for _, row in cards.iterrows():
        st.session_state.card_history.setdefault(row["Name"], []).append({
            "Season": season_num,
            "W": row["W"], "L": row["L"], "OVR": row["OVR"]
        })

    # Save standings snapshot
    st.session_state.standings_snapshots[season_num] = cards.sort_values(
        ["W","OVR"], ascending=False).reset_index(drop=True)

    st.session_state.cards = cards

def color_grade(val):
    colors = {"S+":"#FFD700","S":"#FF8C00","A":"#4CAF50","B":"#2196F3","C":"#B0BEC5"}
    return f"background-color:{colors.get(val,'white')};color:black;font-weight:bold;"

# -------------------- MAIN APP --------------------
st.title("Clash Royale – League Sim (Enhanced UI)")

st.session_state.cards["OVR"] = st.session_state.cards.apply(calculate_ovr, axis=1)
st.session_state.cards["Grade"] = st.session_state.cards["OVR"].apply(assign_grade)

main, balance, history, retired, addcard, profiles = st.tabs([
    "Card Stats","Balance Changes","History","Retired Cards","Add Card","Player Info"
])

with main:
    st.header("📊 Current Standings")
    standings = st.session_state.cards.sort_values(["W","OVR"], ascending=False).reset_index(drop=True)
    st.dataframe(standings.style.applymap(color_grade, subset=["Grade"]))
    if st.button("▶️ Simulate Season"):
        simulate_season()
        st.success("Season simulated! Standings saved in History.")

with balance:
    st.header("⚖️ Balance Changes (Buffs & Nerfs)")

    st.subheader("📊 Current Standings")
    st.dataframe(st.session_state.cards.sort_values(["W","OVR"],ascending=False))

    edited = st.data_editor(
        st.session_state.cards[["Emoji","Name","AtkDmg","AtkSpd","Range","HP"]],
        num_rows="dynamic",
        key="balance_editor"
    )

    if st.button("Save All Changes"):
        season_num = len(st.session_state.season_history)
        for idx,row in edited.iterrows():
            before = st.session_state.cards.loc[idx,["AtkDmg","AtkSpd","Range","HP"]].to_dict()
            after = row[["AtkDmg","AtkSpd","Range","HP"]].to_dict()
            if before != after:
                diffs = []
                for stat in before:
                    if after[stat] > before[stat]:
                        diffs.append(f"{stat} ↑")
                    elif after[stat] < before[stat]:
                        diffs.append(f"{stat} ↓")
                st.session_state.balance_history.append({
                    "Card": row["Name"],
                    "Before": before, "After": after,
                    "Change": ", ".join(diffs),
                    "Season": season_num
                })
        st.session_state.cards.update(edited)
        st.success("Balance changes saved!")

with history:
    st.header("📜 Balance Change History")
    if st.session_state.balance_history:
        df = pd.DataFrame([{
            "Card": h["Card"],
            "Change": h["Change"],
            "Season": h["Season"]
        } for h in st.session_state.balance_history])
        st.table(df)
    else:
        st.info("No balance changes yet.")

    st.header("🏆 Season History")
    if st.session_state.season_history:
        st.table(pd.DataFrame(st.session_state.season_history))
        season_choice = st.selectbox("View standings from season:", options=list(st.session_state.standings_snapshots.keys()))
        st.dataframe(st.session_state.standings_snapshots[season_choice].style.applymap(color_grade, subset=["Grade"]))
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
    emoji = st.text_input("Emoji","⚔️")
    name = st.text_input("Name", f"Custom Card {len(st.session_state.cards)+1}")
    dmg = st.number_input("Attack Damage",50,1000,200)
    spd = st.number_input("Attack Speed",0.5,3.0,1.5,step=0.1)
    rng = st.number_input("Range",0.5,10.0,3.0,step=0.1)
    hp = st.number_input("HP",100,5000,800)
    if st.button("Add Card"):
        new_card = {"Emoji":emoji,"Name":name,"AtkDmg":dmg,"AtkSpd":spd,
                    "Range":rng,"HP":hp,"W":0,"L":0,"OVR":0,"Grade":"C"}
        st.session_state.cards = pd.concat([st.session_state.cards,pd.DataFrame([new_card])],ignore_index=True)
        st.success(f"{name} added!")

with profiles:
    st.header("📖 Player Info Pages")
    for i,row in st.session_state.cards.iterrows():
        if st.button(f"View {row['Name']}"):
            st.subheader(f"{row['Emoji']} {row['Name']} – Profile")
            st.write(f"**Stats:** AtkDmg {row['AtkDmg']}, AtkSpd {row['AtkSpd']}, Range {row['Range']}, HP {row['HP']}, OVR {row['OVR']} ({row['Grade']})")

            if st.button(f"Retire {row['Name']}"):
                st.session_state.retired.append(row)
                st.session_state.cards = st.session_state.cards.drop(i)
                st.warning(f"{row['Name']} retired!")

            if row["Name"] in st.session_state.card_history:
                st.write("**Season Performance:**")
                st.table(pd.DataFrame(st.session_state.card_history[row["Name"]]))
            else:
                st.info("No seasons played yet.")

            changes = [h for h in st.session_state.balance_history if h["Card"] == row["Name"]]
            if changes:
                st.write("**Balance Changes:**")
                st.table(pd.DataFrame([{
                    "Season":h["Season"],"Change":h["Change"]
                } for h in changes]))
            else:
                st.info("No buffs/nerfs recorded.")
