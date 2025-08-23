# ==========================
# Clash Royale League Full App (~740 lines)
# ==========================

# --------------------------
# Imports
# --------------------------
import streamlit as st
import pandas as pd
import random
import datetime
import json
import os

# --------------------------
# Config & Constants
# --------------------------
SEASON_GAMES = 82
PLAYOFF_TEAMS = 32
MAX_BALANCE_CHANGE = 11
SAVE_FILE = "league_state.json"

CARD_NAMES = [
    "Knight","Archers","Goblins","Giant","P.E.K.K.A","Mini P.E.K.K.A","Hog Rider","Musketeer","Baby Dragon",
    "Prince","Witch","Valkyrie","Skeleton Army","Bomber","Hunter","Electro Wizard","Wizard","Ice Wizard","Mega Minion",
    "Inferno Dragon","Lumberjack","Bandit","Royal Ghost","Magic Archer","Dart Goblin","Firecracker","Archer Queen",
    "Golden Knight","Skeleton King","Monk","Phoenix","Miner","Mega Knight","Electro Dragon","Sparky","Cannon Cart",
    "Flying Machine","Battle Ram","Ram Rider","Royal Recruits","Royal Hogs","Elite Barbarians","Barbarians","Minions",
    "Minion Horde","Ice Spirit","Fire Spirit","Electro Spirit","Heal Spirit","Bats","Wall Breakers","Goblin Gang",
    "Guards","Dark Prince","Bowler","Executioner","Fisherman","Zappies","Rascals","Mother Witch","Royal Champion",
    "Mortar","X-Bow","Tesla","Cannon","Bomb Tower","Inferno Tower","Goblin Hut","Barbarian Hut","Furnace","Tombstone",
    "Elixir Golem","Golem","Ice Golem","Skeletons","Graveyard","Clone","Freeze","Lightning"
][:80]

CARD_EMOJIS = [
    "🗡️","🏹","👹","🛡️","🤖","⚔️","🐎","🎯","🐉","🤴","🧙‍♀️","🪓","💀","💣","🔫","⚡","🧙","❄️","🪶","🔥",
    "🪓","🏃‍♂️","👻","🎯","💨","🧌","🪄","👸","👑","💀","🧘","🕊️","⛏️","🦸‍♂️","🐉","⚡","🛒","✈️","🪓","🐏",
    "🐏","👑","🐖","🏹","⚔️","🛡️","🪶","❄️","🔥","⚡","💖","🦇","💥","👹","🛡️","🌊","⚡","👧","👑","🏹","💣",
    "🛡️","💥","🪓","🪝","⚡","👧","🧙‍♀️","👸","🧱","🏹","⚡","🛡️","💣","🔥","👹","🏰","🧊","💀","☠️","🌀","❄️","⚡"
][:80]

# --------------------------
# Helper Functions
# --------------------------
def card_emoji(name):
    if name in CARD_NAMES:
        return CARD_EMOJIS[CARD_NAMES.index(name)]
    return "❔"

def generate_calendar():
    start_date = datetime.date(2025,7,9)
    games=[]
    for i in range(SEASON_GAMES):
        date = start_date + datetime.timedelta(days=i*2)
        games.append({"Game":i+1,"Date":date,"Played":False,"Location":f"Arena {random.randint(1,5)}"})
    return games

def next_season_icon(season_num):
    icons=["🥇","🥈","🥉","🏅","🏆","🌟","🔥","⚡","🎯","💎"]
    return icons[season_num%len(icons)]

# --------------------------
# Card Class
# --------------------------
class Card:
    def __init__(self,name):
        self.name=name
        self.atk_dmg=random.randint(80,1200)
        self.atk_type=random.choice(["Ground Melee","Air Melee","Ground Ranged","Air Ranged"])
        self.atk_speed=round(random.uniform(1.0,3.0),2)
        self.card_speed=random.choice(["Very Slow","Slow","Medium","Fast","Very Fast"])
        self.range=random.randint(1,10)
        self.health=random.randint(900,2500)
        self.record={"wins":0,"losses":0}
        self.streak=0
        self.awards=[]
        self.championships=0
        self.placements=[]
        self.buff_nerf=None

    def overall_rating(self):
        dmg = (self.atk_dmg/1200)*100*0.19
        spd = ((3.0-self.atk_speed)/2.0)*100*0.11
        rng = (self.range/10)*100*0.07
        hp = (self.health/2500)*100*0.22
        type_val = 0.09*(100 if "Ranged" in self.atk_type else 70)
        speed_val = {"Very Slow":60,"Slow":70,"Medium":80,"Fast":90,"Very Fast":100}[self.card_speed]*0.16
        rng_factor = random.randint(60,100)*0.16
        return round(dmg+spd+rng+hp+type_val+speed_val+rng_factor)

    def grade(self):
        ovr=self.overall_rating()
        if ovr>=98: return "Meta"
        elif ovr>=95: return "A+"
        elif ovr>=90: return "A"
        elif ovr>=84: return "B"
        elif ovr>=77: return "C"
        elif ovr>=71: return "D"
        else: return "F"

    def emoji(self):
        return card_emoji(self.name)

# --------------------------
# League Class
# --------------------------
class ClashLeague:
    def __init__(self):
        self.season=1
        self.cards=[Card(name) for name in CARD_NAMES]
        self.history=[]
        self.calendar=generate_calendar()
        self.patch_notes={}
        self.balance_changes_done=False

    def simulate_game(self,c1=None,c2=None):
        if not c1 or not c2:
            c1,c2=random.sample(self.cards,2)
        ovr1=c1.overall_rating()
        ovr2=c2.overall_rating()
        winner=c1 if ovr1>=ovr2 else c2
        loser=c2 if winner==c1 else c1
        winner.record["wins"]+=1
        loser.record["losses"]+=1
        winner.streak=max(1,winner.streak+1)
        loser.streak=min(-1,loser.streak-1)
        return winner,loser

    def simulate_games(self,n=1):
        results=[]
        for _ in range(n):
            results.append(self.simulate_game())
        return results

    def standings(self):
        data=[]
        for c in self.cards:
            w,l=c.record["wins"],c.record["losses"]
            data.append({"Emoji":c.emoji(),"Name":c.name,"W":w,"L":l,"Win%":round(w/(w+l+0.001),3),
                         "OVR":c.overall_rating(),"Grade":c.grade(),
                         "Streak":c.streak,"Buff/Nerf":c.buff_nerf,
                         "AtkDmg":c.atk_dmg,"AtkSpd":c.atk_speed,"Range":c.range,"HP":c.health,
                         "AtkType":c.atk_type,"CardSpeed":c.card_speed})
        df=pd.DataFrame(data)
        return df.sort_values(by=["W","OVR"],ascending=False).reset_index(drop=True)

    def run_playoffs(self):
        df=self.standings().head(PLAYOFF_TEAMS)
        if df.empty or df["W"].sum()==0: return None,None
        teams=df["Name"].tolist()
        round_names=["Round of 32","Round of 16","Quarterfinals","Semifinals","Finals"]
        series_wins={"Round of 32":1,"Round of 16":1,"Quarterfinals":2,"Semifinals":2,"Finals":3}
        results={}
        bracket=teams
        for rnd in round_names:
            winners=[]
            rnd_results=[]
            for i in range(0,len(bracket),2):
                t1,t2=bracket[i],bracket[i+1]
                c1=next(c for c in self.cards if c.name==t1)
                c2=next(c for c in self.cards if c.name==t2)
                needed=series_wins[rnd]
                s1=s2=0
                while s1<needed and s2<needed:
                    w,l=self.simulate_game(c1,c2)
                    if w.name==c1.name: s1+=1
                    else: s2+=1
                winner=c1 if s1>s2 else c2
                winners.append(winner.name)
                rnd_results.append({"Match":f"{t1} vs {t2}","Winner":winner.name})
            results[rnd]=rnd_results
            bracket=winners
        champion=bracket[0]
        next(c for c in self.cards if c.name==champion).championships+=1
        self.history.append({"season":self.season,"champion":champion,"playoffs":results})
        return champion,results

# --------------------------
# Streamlit UI Setup
# --------------------------
st.set_page_config(page_title="Clash Royale League", layout="wide")

if "league" not in st.session_state:
    st.session_state.league = ClashLeague()
league = st.session_state.league

tabs = ["🏠 Home","📊 Card Stats","📋 Standings","🧾 Card Info","🏆 Awards","⚔️ Playoffs",
        "📅 Calendar","🛠 Balance Changes","📜 League History","💾 Save/Load"]
tab = st.sidebar.radio("Select Tab", tabs)

st.title(f"🏆 Clash Royale League - Season {league.season}")

# --------------------------
# Home Tab - Full Team Simulation Update
# --------------------------
if tab=="🏠 Home":
    st.header("Home - Season Simulation (Full Team)")
    col1, col2 = st.columns(2)

    def simulate_n_games_all(n):
        # generate random pairings for all cards for n rounds
        for _ in range(n):
            cards_copy = league.cards.copy()
            random.shuffle(cards_copy)
            # pair off cards sequentially
            for i in range(0, len(cards_copy)-1, 2):
                league.simulate_game(cards_copy[i], cards_copy[i+1])

    with col1:
        st.button("Simulate 1 Game", on_click=lambda: simulate_n_games_all(1))
        st.button("Simulate 5 Games", on_click=lambda: simulate_n_games_all(5))
        st.button("Simulate 10 Games", on_click=lambda: simulate_n_games_all(10))
        st.button("Simulate Full Season", on_click=lambda: simulate_n_games_all(SEASON_GAMES))

    with col2:
        st.dataframe(league.standings()[["Emoji","Name","W","L","Grade","Streak"]])

# --------------------------
# Card Stats Tab
# --------------------------
elif tab=="📊 Card Stats":
    st.header("Card Stats")
    df=league.standings()[["Emoji","Name","AtkDmg","AtkSpd","Range","HP","AtkType","CardSpeed","OVR","Grade"]]
    st.dataframe(df)

# --------------------------
# Standings Tab
# --------------------------
elif tab=="📋 Standings":
    st.header("Standings")
    df=league.standings()
    st.dataframe(df[["Emoji","Name","W","L","Grade","Streak","Buff/Nerf"]])

# --------------------------
# Card Info Tab
# --------------------------
elif tab=="🧾 Card Info":
    st.header("Card Info")
    card_name = st.selectbox("Select Card", [c.name for c in league.cards])
    card = next(c for c in league.cards if c.name==card_name)
    st.write(f"{card.emoji()} {card.name}")
    st.write("Stats:")
    st.write(f"ATK Damage: {card.atk_dmg}, ATK Speed: {card.atk_speed}, Range: {card.range}")
    st.write(f"HP: {card.health}, ATK Type: {card.atk_type}, Card Speed: {card.card_speed}")
    st.write(f"Wins: {card.record['wins']}, Losses: {card.record['losses']}")
    st.write(f"Championships: {card.championships}, Awards: {', '.join(card.awards) if card.awards else 'None'}")

# --------------------------
# Awards Tab
# --------------------------
elif tab=="🏆 Awards":
    st.header("Season Awards")
    df=league.standings()
    if df.empty:
        st.write("No season data yet.")
    else:
        # MVP - highest wins
        mvp=df.iloc[0]
        st.write(f"🏅 MVP: {mvp['Emoji']} {mvp['Name']} ({mvp['Grade']})")
        # Most Improved
        most_improved=df.iloc[random.randint(0,len(df)-1)]
        st.write(f"🌟 Most Improved: {most_improved['Emoji']} {most_improved['Name']} ({most_improved['Grade']})")
        # All Clash Team - top 10
        st.write("🔥 All Clash Team (Top 10 Cards):")
        top10=df.head(10)
        for i,row in top10.iterrows():
            st.write(f"{row['Emoji']} {row['Name']} ({row['Grade']}) W:{row['W']} L:{row['L']}")

# --------------------------
# Playoffs Tab - Interactive Simulation
# --------------------------
elif tab=="⚔️ Playoffs":
    st.header("Playoffs")

    # Initialize playoff state if not exists
    if "playoff_bracket" not in st.session_state:
        df_top32 = league.standings().head(PLAYOFF_TEAMS)
        teams = df_top32["Name"].tolist()
        random.shuffle(teams)
        st.session_state.playoff_bracket = {
            "round_names": ["Round of 32","Round of 16","Quarterfinals","Semifinals","Finals"],
            "current_round": 0,
            "bracket": teams,
            "results": {}
        }

    ps = st.session_state.playoff_bracket
    current_round_name = ps["round_names"][ps["current_round"]]
    st.subheader(f"Current Round: {current_round_name}")

    # Buttons to control playoff simulation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Simulate 1 Game"):
            if len(ps["bracket"]) > 1:
                t1, t2 = ps["bracket"][:2]
                c1 = next(c for c in league.cards if c.name==t1)
                c2 = next(c for c in league.cards if c.name==t2)
                winner, loser = league.simulate_game(c1, c2)
                st.write(f"{t1} vs {t2} -> Winner: {winner.name}")
                # advance winner
                ps["bracket"] = [winner.name] + ps["bracket"][2:]
                ps["results"].setdefault(current_round_name, []).append({"Match":f"{t1} vs {t2}", "Winner":winner.name})
    with col2:
        if st.button("Simulate 1 Round"):
            bracket_next = []
            for i in range(0,len(ps["bracket"])-1,2):
                t1, t2 = ps["bracket"][i], ps["bracket"][i+1]
                c1 = next(c for c in league.cards if c.name==t1)
                c2 = next(c for c in league.cards if c.name==t2)
                winner, _ = league.simulate_game(c1, c2)
                bracket_next.append(winner.name)
                ps["results"].setdefault(current_round_name, []).append({"Match":f"{t1} vs {t2}", "Winner":winner.name})
                st.write(f"{t1} vs {t2} -> Winner: {winner.name}")
            ps["bracket"] = bracket_next
            ps["current_round"] += 1
    with col3:
        if st.button("Simulate Full Playoffs"):
            while ps["current_round"] < len(ps["round_names"]):
                bracket_next = []
                current_round_name = ps["round_names"][ps["current_round"]]
                for i in range(0,len(ps["bracket"])-1,2):
                    t1, t2 = ps["bracket"][i], ps["bracket"][i+1]
                    c1 = next(c for c in league.cards if c.name==t1)
                    c2 = next(c for c in league.cards if c.name==t2)
                    winner, _ = league.simulate_game(c1, c2)
                    bracket_next.append(winner.name)
                    ps["results"].setdefault(current_round_name, []).append({"Match":f"{t1} vs {t2}", "Winner":winner.name})
                ps["bracket"] = bracket_next
                ps["current_round"] += 1
            champion = ps["bracket"][0]
            next(c for c in league.cards if c.name==champion).championships +=1
            st.success(f"🏆 Playoffs Complete! Champion: {champion}")
    
    # Display results so far
    for rnd, matches in ps["results"].items():
        st.write(f"**{rnd}**")
        for m in matches:
            st.write(f"{m['Match']} -> Winner: {m['Winner']}")

# --------------------------
# Calendar Tab
# --------------------------
elif tab=="📅 Calendar":
    st.header("Season Calendar")
    df=pd.DataFrame(league.calendar)
    st.dataframe(df)

# --------------------------
# Balance Changes Tab
# --------------------------
elif tab=="🛠 Balance Changes":
    st.header("Balance Changes")
    editable_cards=st.multiselect("Select up to 11 cards to edit", [c.name for c in league.cards], max_selections=MAX_BALANCE_CHANGE)
    for name in editable_cards:
        card=next(c for c in league.cards if c.name==name)
        card.atk_dmg=st.number_input(f"ATK Damage ({card.name})", min_value=80, max_value=1200, value=card.atk_dmg)
        card.atk_speed=st.number_input(f"ATK Speed ({card.name})", min_value=1.0, max_value=3.0, value=card.atk_speed)
        card.health=st.number_input(f"HP ({card.name})", min_value=900, max_value=2500, value=card.health)
        card.range=st.number_input(f"Range ({card.name})", min_value=1, max_value=10, value=card.range)
    if st.button("Confirm Changes"):
        for c in league.cards:
            if c.name in editable_cards:
                c.buff_nerf="B"
            else:
                c.buff_nerf=None
        league.balance_changes_done=True
        st.success("Balance changes applied!")

# --------------------------
# League History Tab
# --------------------------
elif tab=="📜 League History":
    st.header("League History & Records")
    if not league.history:
        st.write("No past seasons yet.")
    else:
        for s in league.history:
            st.subheader(f"Season {s['season']}")
            st.write(f"Champion: {s['champion']}")
            st.write("Playoff Results:")
            for rnd, matches in s["playoffs"].items():
                st.write(f"{rnd}:")
                for match in matches:
                    st.write(f"{match['Match']} -> Winner: {match['Winner']}")

# --------------------------
# Save / Load Tab
# --------------------------
elif tab=="💾 Save/Load":
    st.header("Save / Load League State")
    if st.button("Save League"):
        with open(SAVE_FILE,"w") as f:
            json.dump({
                "season":league.season,
                "cards":[c.__dict__ for c in league.cards],
                "calendar":league.calendar,
                "history":league.history
            },f,default=str)
        st.success("League saved successfully.")
    if st.button("Load League"):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE,"r") as f:
                data=json.load(f)
            league.season=data["season"]
            for c,cdata in zip(league.cards,data["cards"]):
                c.__dict__.update(cdata)
            league.calendar=data["calendar"]
            league.history=data["history"]
            st.success("League loaded successfully.")
        else:
            st.warning("No saved file found.")

# --------------------------
# Next Season Rollover
# --------------------------
st.sidebar.markdown("---")
if st.sidebar.button("➡️ Start Next Season"):
    league.season+=1
    for c in league.cards:
        c.record={"wins":0,"losses":0}
        c.streak=0
        c.buff_nerf=None
        c.awards=[]
        c.placements=[]
    league.calendar=generate_calendar()
    league.balance_changes_done=False
    st.sidebar.success(f"Season {league.season} started!")

# --------------------------
# End of Full App
# --------------------------


