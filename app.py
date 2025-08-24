import streamlit as st
import pandas as pd
import random
import json
import os

# -------------------- SAVE/LOAD --------------------
SAVE_FILE = "saved_game.json"

def save_game():
    data = {
        "cards": st.session_state.cards.to_dict(orient="records"),
        "balance_history": st.session_state.balance_history,
        "season_history": st.session_state.season_history,
        "removed_cards": st.session_state.removed_cards,
        "card_history": st.session_state.card_history,
        "standings_snapshots": {k: v.to_dict(orient="records") for k,v in st.session_state.standings_snapshots.items()}
    }
    with open(SAVE_FILE,"w") as f:
        json.dump(data, f, indent=2)

def load_game():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE,"r") as f:
                data = json.load(f)
            st.session_state.cards = pd.DataFrame(data["cards"])
            st.session_state.balance_history = data["balance_history"]
            st.session_state.season_history = data["season_history"]
            st.session_state.removed_cards = data["removed_cards"]
            st.session_state.card_history = data["card_history"]
            st.session_state.standings_snapshots = {int(k): pd.DataFrame(v) for k,v in data["standings_snapshots"].items()}
        except (json.JSONDecodeError, KeyError):
            st.warning("Saved game file is empty or corrupted. Starting a new game...")
            # Reset session state
            st.session_state.cards = pd.DataFrame()
            st.session_state.balance_history = []
            st.session_state.season_history = []
            st.session_state.removed_cards = []
            st.session_state.card_history = {}
            st.session_state.standings_snapshots = {}

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

# -------------------- SESSION INIT --------------------
if "cards" not in st.session_state:
    chosen = random.sample(CARD_POOL, 80)
    emojis = ["⚔️","🏹","🐉","🧙","👹","🛡️","🔥","❄️","💀","⚡"]
    cards_data = []
    idx = 0
    for min_ovr,max_ovr in OVR_RANGES:
        for _ in range(20):
            ovr = random.randint(min_ovr,max_ovr)
            dmg = random.randint(ovr*2, ovr*4)
            spd = round(random.uniform(1.0,1.8),1)
            rng = round(random.uniform(2.0,5.0),1)
            hp = random.randint(ovr*10, ovr*20)
            cards_data.append({
                "Emoji": random.choice(emojis),
                "Name": chosen[idx],
                "AtkDmg": dmg,
                "AtkSpd": spd,
                "Range": rng,
                "HP": hp,
                "W":0, "L":0, "OVR":ovr, "Grade":"B",
                "Seasons":0
            })
            idx += 1
    st.session_state.cards = pd.DataFrame(cards_data)
    st.session_state.balance_history = []
    st.session_state.season_history = []
    st.session_state.removed_cards = []
    st.session_state.card_history = {}
    st.session_state.standings_snapshots = {}
else:
    load_game()

# -------------------- FUNCTIONS --------------------
def calculate_ovr(row):
    # Custom formula: dmg 32%, spd 19%, range 19%, hp 30%
    max_dmg = 400
    max_spd = 2.0
    max_range = 5.0
    max_hp = 1500

    dmg_score = (row["AtkDmg"]/max_dmg)*0.32
    spd_score = (row["AtkSpd"]/max_spd)*0.19
    range_score = (row["Range"]/max_range)*0.19
    hp_score = (row["HP"]/max_hp)*0.30

    ovr = (dmg_score + spd_score + range_score + hp_score)*100
    return round(ovr,1)

def assign_grade(ovr):
    if ovr >= 93: return "S+"
    elif ovr >= 88: return "S"
    elif ovr >= 82: return "A"
    elif ovr >= 75: return "B"
    else: return "C"

def simulate_games(n_games=82):
    cards = st.session_state.cards.copy()
    cards["W"], cards["L"] = 0,0
    season_num = len(st.session_state.season_history)+1

    for idx in range(len(cards)):
        opponents = random.choices(cards.index[cards.index != idx], k=n_games)
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

    for _, row in cards.iterrows():
        st.session_state.card_history.setdefault(row["Name"], []).append({
            "Season": season_num, "W": row["W"], "L": row["L"], "OVR": row["OVR"]
        })
        st.session_state.cards.loc[st.session_state.cards["Name"]==row["Name"],"Seasons"] += 1

    st.session_state.standings_snapshots[season_num] = cards.sort_values(["W","OVR"], ascending=False).reset_index(drop=True)
    st.session_state.cards = cards
    save_game()

def rank_table(df):
    df = df.copy()
    df.insert(0,"Rank",range(1,len(df)+1))
    for col in ["AtkSpd","Range"]:
        if col in df.columns:
            df[col] = df[col].round(1)
    return df

def color_grade(val):
    colors = {"S+":"#FFD700","S":"#FF8C00","A":"#4CAF50","B":"#2196F3","C":"#B0BEC5"}
    return f"background-color:{colors.get(val,'white')};color:black;font-weight:bold;"

def fully_remove_card(name):
    idx = st.session_state.cards[st.session_state.cards["Name"]==name].index
    if len(idx) == 0: return
    idx = idx[0]
    st.session_state.removed_cards.append(st.session_state.cards.loc[idx].to_dict())
    st.session_state.cards = st.session_state.cards.drop(idx).reset_index(drop=True)
    if name in st.session_state.card_history: del st.session_state.card_history[name]
    st.session_state.balance_history = [h for h in st.session_state.balance_history if h["Card"] != name]
    for season, df in st.session_state.standings_snapshots.items():
        st.session_state.standings_snapshots[season] = df[df["Name"] != name].reset_index(drop=True)
    save_game()

# -------------------- MAIN APP --------------------
st.title("⚔️ Clash Royale – League Simulator ⚔️")
st.session_state.cards["Grade"] = st.session_state.cards["OVR"].apply(assign_grade)

main, balance, history, removed_tab, addcard, profiles = st.tabs([
    "Card Stats","Balance Changes","History","Removed Cards","Add Card","Player Info"
])

# -------------------- MAIN STANDINGS --------------------
with main:
    st.subheader("📊 Current Standings")
    standings = rank_table(st.session_state.cards.sort_values(["W","OVR"], ascending=False))
    st.dataframe(standings.style.applymap(color_grade, subset=["Grade"]))

    if st.button("▶️ Simulate Full Season", key="simulate_season"):
        simulate_games(82)
        st.success("Full season simulated! Standings updated.")

# -------------------- BALANCE CHANGES --------------------
with balance:
    st.subheader("⚖️ Balance Changes & Standings")
    st.markdown("### 📊 Current Standings Snapshot")
    quick_standings = rank_table(st.session_state.cards.sort_values(["W","OVR"], ascending=False))
    st.dataframe(quick_standings.style.applymap(color_grade, subset=["Grade"]))

    search_name = st.text_input("🔍 Search Card")
    filtered = st.session_state.cards
    if search_name: filtered = filtered[filtered["Name"].str.contains(search_name, case=False)]

    st.write("Edit card stats and apply balance changes:")
    for i, row in filtered.iterrows():
        st.markdown(f"**{row['Emoji']} {row['Name']}** (OVR: {row['OVR']}, Grade: {row['Grade']})")
        col1,col2,col3,col4 = st.columns(4)
        with col1: new_dmg = st.number_input(f"AtkDmg {row['Name']}", 1,2000,int(row['AtkDmg']), key=f"dmg_{row['Name']}")
        with col2: new_spd = st.number_input(f"AtkSpd {row['Name']}",0.1,5.0,float(row['AtkSpd']),0.1,key=f"spd_{row['Name']}")
        with col3: new_rng = st.number_input(f"Range {row['Name']}",0.1,20.0,float(row['Range']),0.1,key=f"rng_{row['Name']}")
        with col4: new_hp = st.number_input(f"HP {row['Name']}",1,10000,int(row['HP']),key=f"hp_{row['Name']}")
        if st.button(f"Apply Changes", key=f"apply_{row['Name']}"):
            old_stats = row[["AtkDmg","AtkSpd","Range","HP"]].to_dict()
            st.session_state.cards.loc[st.session_state.cards["Name"]==row['Name'], ["AtkDmg","AtkSpd","Range","HP"]] = [new_dmg,new_spd,new_rng,new_hp]
            ovr = calculate_ovr({"AtkDmg":new_dmg,"AtkSpd":new_spd,"Range":new_rng,"HP":new_hp})
            grade = assign_grade(ovr)
            st.session_state.cards.loc[st.session_state.cards["Name"]==row['Name'], ["OVR","Grade"]] = [ovr, grade]
            st.session_state.balance_history.append({
                "Card": row['Name'],
                "Season": len(st.session_state.season_history)+1,
                "Before": old_stats,
                "After": {"AtkDmg":new_dmg,"AtkSpd":new_spd,"Range":new_rng,"HP":new_hp},
                "Change": {k: new_dmg-old_stats[k] if k=="AtkDmg" else new_spd-old_stats[k] if k=="AtkSpd" else new_rng-old_stats[k] if k=="Range" else new_hp-old_stats[k] for k in old_stats}
            })
            save_game()
            st.success(f"Updated {row['Name']}! New OVR: {ovr}, Grade: {grade}")

# -------------------- HISTORY --------------------
with history:
    st.subheader("📜 Season History")
    if st.session_state.season_history:
        st.dataframe(pd.DataFrame(st.session_state.season_history))
        latest_season = max(st.session_state.standings_snapshots.keys())
        st.dataframe(rank_table(st.session_state.standings_snapshots[latest_season]).style.applymap(color_grade, subset=["Grade"]))
    else:
        st.dataframe(pd.DataFrame(columns=["Season","Champion","Record","OVR"]))

    st.subheader("⚖️ Balance Change History (Clean View)")
    if st.session_state.balance_history:
        clean_history = []
        for h in st.session_state.balance_history:
            before = {k: round(v,1) for k,v in h["Before"].items()}
            after = {k: round(v,1) for k,v in h["After"].items()}
            change = {k: round(v,1) for k,v in h["Change"].items()}
            clean_history.append({
                "Card": h["Card"], "Season": h["Season"],
                "Before": str(before), "After": str(after), "Change": str(change)
            })
        st.dataframe(pd.DataFrame(clean_history))
    else:
        st.info("No balance changes yet.")

# -------------------- REMOVED CARDS --------------------
with removed_tab:
    st.subheader("🚪 Removed Cards")
    if st.session_state.removed_cards:
        removed_df = pd.DataFrame(st.session_state.removed_cards)
        st.dataframe(rank_table(removed_df))
    else:
        st.dataframe(pd.DataFrame(columns=st.session_state.cards.columns))

# -------------------- ADD NEW CARD --------------------
with addcard:
    st.subheader("➕ Add New Card")
    st.dataframe(rank_table(st.session_state.cards.sort_values(["W","OVR"], ascending=False)).style.applymap(color_grade, subset=["Grade"]))
    emoji = st.text_input("Emoji","⚔️")
    name = st.text_input("Name", f"Custom Card {len(st.session_state.cards)+1}")
    dmg = st.number_input("Attack Damage",50,1000,200)
    spd = st.number_input("Attack Speed",0.5,3.0,1.5,0.1)
    rng = st.number_input("Range",0.5,10.0,3.0,0.1)
    hp = st.number_input("HP",100,5000,800)
    if st.button("➕ Add Card", key="add_card"):
        ovr = calculate_ovr({"AtkDmg":dmg,"AtkSpd":spd,"Range":rng,"HP":hp})
        grade = assign_grade(ovr)
        new_card = {"Emoji":emoji,"Name":name,"AtkDmg":dmg,"AtkSpd":spd,"Range":rng,"HP":hp,"W":0,"L":0,"OVR":ovr,"Grade":grade,"Seasons":0}
        st.session_state.cards = pd.concat([st.session_state.cards,pd.DataFrame([new_card])],ignore_index=True)
        save_game()
        st.success(f"{name} added! OVR: {ovr}, Grade: {grade}")

# -------------------- PLAYER PROFILES --------------------
with profiles:
    st.subheader("📖 Player Info Pages")
    if st.session_state.cards.empty:
        st.dataframe(pd.DataFrame(columns=st.session_state.cards.columns))
    else:
        for i,row in st.session_state.cards.iterrows():
            if st.button(f"{row['Emoji']} {row['Name']}", key=f"view_{row['Name']}"):
                st.write(f"{row['Emoji']} **{row['Name']}**")
                st.write(f"Stats: AtkDmg {row['AtkDmg']}, AtkSpd {row['AtkSpd']}, Range {row['Range']}, HP {row['HP']}, OVR {row['OVR']} ({row['Grade']})")
                st.write(f"Seasons Played: {row['Seasons']}")
                if st.button(f"Remove Card", key=f"remove_{row['Name']}"):
                    fully_remove_card(row['Name'])
                    st.warning(f"{row['Name']} fully removed from all data!")

