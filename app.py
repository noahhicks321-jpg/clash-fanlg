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

OVR_RANGES = [(60,70),(70,80),(80,89),(90,99)]

if "cards" not in st.session_state:
    chosen = random.sample(CARD_POOL, 80)
    emojis = ["⚔️","🏹","🐉","🧙","👹","🛡️","🔥","❄️","💀","⚡"]
    cards_data = []
    idx = 0
    for min_ovr,max_ovr in OVR_RANGES:
        for _ in range(20):
            ovr = random.randint(min_ovr,max_ovr)
            dmg = random.randint(ovr*2,ovr*4)
            spd = round(random.uniform(1.0,1.8),1)
            rng = round(random.uniform(2.0,5.0),1)
            hp  = random.randint(ovr*10,ovr*20)
            cards_data.append({
                "Emoji": random.choice(emojis),
                "Name": chosen[idx],
                "AtkDmg": dmg,
                "AtkSpd": spd,
                "Range": rng,
                "HP": hp,
                "W":0, "L":0, "OVR":ovr, "Grade":"B", "Seasons":0
            })
            idx += 1
    st.session_state.cards = pd.DataFrame(cards_data)
    st.session_state.balance_history = []
    st.session_state.season_history = []
    st.session_state.removed = []  # cards removed from season
    st.session_state.card_history = {}
    st.session_state.standings_snapshots = {}

# -------------------- FUNCTIONS --------------------
def calculate_ovr(row):
    raw = (row["AtkDmg"]*0.4 + (1/row["AtkSpd"])*100*0.2 + row["Range"]*20*0.1 + row["HP"]*0.3)/10
    return max(65, min(95, round(raw,1)))

def assign_grade(ovr):
    if ovr >= 93: return "S+"
    elif ovr >= 88: return "S"
    elif ovr >= 82: return "A"
    elif ovr >= 75: return "B"
    else: return "C"

def simulate_games(num_games):
    cards = st.session_state.cards.copy()
    cards["W"], cards["L"] = 0,0
    season_num = len(st.session_state.season_history)+1

    for idx in range(len(cards)):
        opponents = random.choices(cards.index[cards.index != idx], k=num_games)
        for opp in opponents:
            score_self = cards.loc[idx,"OVR"]*0.78 + random.uniform(-5,5)*0.22
            score_opp = cards.loc[opp,"OVR"]*0.78 + random.uniform(-5,5)*0.22
            if score_self > score_opp:
                cards.loc[idx,"W"] += 1
                cards.loc[opp,"L"] += 1
            else:
                cards.loc[idx,"L"] += 1
                cards.loc[opp,"W"] += 1

    # Update season counters
    cards["Seasons"] += 1

    champion = cards.sort_values(["W","OVR"], ascending=False).iloc[0]
    st.session_state.season_history.append({
        "Season": season_num,
        "Champion": champion["Name"],
        "Record": f"{champion['W']}-{champion['L']}",
        "OVR": champion["OVR"]
    })

    for _, row in cards.iterrows():
        st.session_state.card_history.setdefault(row["Name"], []).append({
            "Season": season_num, "W": row["W"], "L": row["L"], "OVR": row["OVR"]
        })

    st.session_state.standings_snapshots[season_num] = cards.sort_values(
        ["W","OVR"], ascending=False).reset_index(drop=True)

    st.session_state.cards = cards

def color_grade(val):
    colors = {"S+":"#FFD700","S":"#FF8C00","A":"#4CAF50","B":"#2196F3","C":"#B0BEC5"}
    return f"background-color:{colors.get(val,'white')};color:black;font-weight:bold;"

def rank_table(df):
    df = df.copy()
    df.insert(0,"Rank",range(1,len(df)+1))
    # Round float columns
    for col in ["AtkSpd","Range","OVR"]:
        if col in df.columns:
            df[col] = df[col].round(1)
    return df

def remove_from_season(name):
    idx = st.session_state.cards[st.session_state.cards["Name"]==name].index[0]
    st.session_state.removed.append(st.session_state.cards.loc[idx].to_dict())
    st.session_state.cards = st.session_state.cards.drop(idx).reset_index(drop=True)

# -------------------- MAIN APP --------------------
st.title("⚔️ Clash Royale – League Simulator ⚔️")

st.session_state.cards["Grade"] = st.session_state.cards["OVR"].apply(assign_grade)

main, balance, history, removed_tab, addcard, profiles = st.tabs([
    "Card Stats","Balance Changes","History","Removed Cards","Add Card","Player Info"
])

with main:
    st.subheader("📊 Current Standings")
    standings = rank_table(st.session_state.cards.sort_values(["W","OVR"], ascending=False))
    st.dataframe(standings.style.applymap(color_grade, subset=["Grade"]))
    sim_choice = st.selectbox("Simulate games:", [1,5,10,25,"Full Season"])
    if st.button("▶️ Simulate"):
        num_games = 82 if sim_choice=="Full Season" else int(sim_choice)
        simulate_games(num_games)
        st.success(f"Simulated {num_games} games!")
        st.experimental_rerun()  # refresh to show updated standings

with balance:
    st.subheader("⚖️ Balance Changes")
    search_name = st.text_input("🔍 Search Card")
    filtered = st.session_state.cards
    if search_name:
        filtered = filtered[filtered["Name"].str.contains(search_name, case=False)]
    st.dataframe(rank_table(filtered.sort_values(["W","OVR"], ascending=False)))

    edited = st.data_editor(
        filtered[["Emoji","Name","AtkDmg","AtkSpd","Range","HP"]],
        num_rows="dynamic",
        key="balance_editor"
    )

    if st.button("💾 Save All Changes"):
        season_num = len(st.session_state.season_history)
        for idx,row in edited.iterrows():
            original_idx = st.session_state.cards[st.session_state.cards["Name"]==row["Name"]].index[0]
            before = st.session_state.cards.loc[original_idx, ["AtkDmg","AtkSpd","Range","HP"]].to_dict()
            after = row[["AtkDmg","AtkSpd","Range","HP"]].to_dict()
            if before != after:
                diffs=[]
                for stat in before:
                    if after[stat] > before[stat]:
                        diffs.append(f"{stat} B")
                    elif after[stat] < before[stat]:
                        diffs.append(f"{stat} N")
                st.session_state.balance_history.append({
                    "Card": row["Name"],
                    "Before": before, "After": after,
                    "Change": ", ".join(diffs),
                    "Season": season_num
                })
            st.session_state.cards.loc[original_idx, ["AtkDmg","AtkSpd","Range","HP"]] = after
        st.success("Balance changes saved!")

with history:
    st.subheader("📜 Season History")
    if st.session_state.season_history:
        st.dataframe(pd.DataFrame(st.session_state.season_history))
        season_choice = st.selectbox("View standings from season:", options=list(st.session_state.standings_snapshots.keys()))
        st.dataframe(rank_table(st.session_state.standings_snapshots[season_choice]).style.applymap(color_grade, subset=["Grade"]))
    else:
        st.info("No seasons simulated yet.")

with removed_tab:
    st.subheader("🚪 Removed Cards")
    if st.session_state.removed:
        removed_df = pd.DataFrame(st.session_state.removed)
        removed_df["Seasons Played"] = removed_df["Seasons"]
        st.dataframe(rank_table(removed_df))
    else:
        st.info("No cards removed.")

with addcard:
    st.subheader("➕ Add New Card")
    emoji = st.text_input("Emoji","⚔️")
    name = st.text_input("Name", f"Custom Card {len(st.session_state.cards)+1}")
    dmg = st.number_input("Attack Damage",50,1000,200)
    spd = st.number_input("Attack Speed",0.5,3.0,1.5,step=0.1)
    rng = st.number_input("Range",0.5,10.0,3.0,step=0.1)
    hp = st.number_input("HP",100,5000,800)
    ovr_preview = calculate_ovr({"AtkDmg":dmg,"AtkSpd":spd,"Range":rng,"HP":hp})
    grade_preview = assign_grade(ovr_preview)
    st.write(f"Card Preview – OVR: {ovr_preview}, Grade: {grade_preview}")
    if st.button("➕ Add Card"):
        new_card = {"Emoji":emoji,"Name":name,"AtkDmg":dmg,"AtkSpd":spd,
                    "Range":rng,"HP":hp,"OVR":ovr_preview,"Grade":grade_preview,"W":0,"L":0,"Seasons":0}
        st.session_state.cards = pd.concat([st.session_state.cards,pd.DataFrame([new_card])],ignore_index=True)
        st.success(f"{name} added!")

with profiles:
    st.subheader("📖 Player Info Pages")
    for i,row in st.session_state.cards.iterrows():
        if st.button(f"View {row['Emoji']} {row['Name']}"):
            st.write(f"{row['Emoji']} **{row['Name']}**")
            st.write(f"Stats: AtkDmg {row['AtkDmg']}, AtkSpd {row['AtkSpd']}, Range {row['Range']}, HP {row['HP']}, OVR {row['OVR']} ({row['Grade']})")
            if st.button(f"Remove from Season {row['Name']}"):
                remove_from_season(row['Name'])
                st.warning(f"{row['Name']} removed from season!")
                st.experimental_rerun()
            if row["Name"] in st.session_state.card_history:
                st.dataframe(pd.DataFrame(st.session_state.card_history[row["Name"]]))
