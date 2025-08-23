# ==========================
# Clash Royale League - Complete Single File App with Emojis & Season Rollover
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

    # --------------------------
    # Game Engine
    # --------------------------
    def simulate_game(self,c1=None,c2=None):
        if not c1 or not c2:
            c1,c2=random.sample(self.cards,2)
        ovr1,c1_val=c1.overall_rating(),c1
        ovr2,c2_val=c2.overall_rating(),c2
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

    # --------------------------
    # Standings
    # --------------------------
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

    # --------------------------
    # Playoffs
    # --------------------------
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

# ==========================
# Streamlit UI Setup
# ==========================
st.set_page_config(page_title="Clash Royale League", layout="wide")

if "league" not in st.session_state:
    st.session_state.league = ClashLeague()
league = st.session_state.league

tabs = ["🏠 Home","📊 Card Stats","📋 Standings","🧾 Card Info","🏆 Awards","⚔️ Playoffs",
        "📅 Calendar","🛠 Balance Changes","📜 League History","💾 Save/Load"]
tab = st.sidebar.radio("Select Tab", tabs)

st.title(f"🏆 Clash Royale League - Season {league.season}")

# --------------------------
# Home Tab
# --------------------------
if tab=="🏠 Home":
    st.subheader("Top 10 Cards")
    top10 = league.standings().head(10)
    for i,row in top10.iterrows():
        st.write(f"{row['Emoji']} {row['Name']} ({row['Grade']}) W:{row['W']} L:{row['L']}")
    st.subheader("Simulate Games")
    col1,col2,col3,col4,col5=st.columns(5)
    if col1.button("1 Game"): league.simulate_games(1)
    if col2.button("5 Games"): league.simulate_games(5)
    if col3.button("10 Games"): league.simulate_games(10)
    if col4.button("40 Games"): league.simulate_games(40)
    if col5.button("Full Season"): league.simulate_games(SEASON_GAMES)
    st.success("Simulation complete. Standings updated.")
    # End season & rollover
    if st.button("End Season & Rollover"):
        # Awards
        df = league.standings()
        mvp = df.iloc[0]
        st.write(f"🏅 MVP: {mvp['Emoji']} {mvp['Name']} ({mvp['Grade']})")
        st.write("🔥 All Clash Team (Top 10):")
        for i,row in df.head(10).iterrows():
            st.write(f"{row['Emoji']} {row['Name']} ({row['Grade']})")
        # Patch notes / Balance summary
        st.write("📈 Trend Summary (Buffs/Nerfs):")
        trends=[]
        for c in league.cards:
            if c.buff_nerf:
                trends.append(f"{c.emoji()} {c.name}: {c.buff_nerf}")
        if trends:
            for t in trends: st.write(t)
        else:
            st.write("No changes this season.")
        # Reset for next season
        for c in league.cards:
            c.record={"wins":0,"losses":0}
            c.streak=0
            c.buff_nerf=None
            c.placements.append(c.grade())
        league.season +=1
        league.calendar=generate_calendar()
        league.balance_changes_done=False
        st.success(f"✅ Season rolled over. Welcome to Season {league.season}!")

# --------------------------
# Card Stats Tab
# --------------------------
elif tab=="📊 Card Stats":
    st.subheader("Card Stats Overview")
    df=league.standings()[["Emoji","Name","AtkDmg","AtkSpd","Range","HP","AtkType","CardSpeed","OVR","Grade"]]
    st.dataframe(df.style.format({"AtkSpd":"{:.2f}"}))

# --------------------------
# Standings Tab
# --------------------------
elif tab=="📋 Standings":
    st.subheader("Season Standings")
    df=league.standings()
    st.dataframe(df[["Emoji","Name","W","L","Win%","Grade","Streak","Buff/Nerf"]])

# --------------------------
# Card Info Tab
# --------------------------
elif tab=="🧾 Card Info":
    st.subheader("Card Profiles")
    card_name = st.selectbox("Select Card", [c.name for c in league.cards])
    c = next(c for c in league.cards if c.name==card_name)
    st.write(f"{c.emoji()} **{c.name}**")
    st.write(f"Wins: {c.record['wins']} Losses: {c.record['losses']} Streak: {c.streak}")
    st.write(f"OVR: {c.overall_rating()} Grade: {c.grade()}")
    st.write(f"AtkDmg: {c.atk_dmg} AtkSpeed: {c.atk_speed} Range: {c.range} HP: {c.health}")
    st.write(f"AtkType: {c.atk_type} CardSpeed: {c.card_speed}")
    st.write(f"Championships Won: {c.championships}")
    if c.awards: st.write("Awards: "+" | ".join(c.awards))
    if c.placements: st.write("Previous Placements:", c.placements)

# --------------------------
# Awards Tab
# --------------------------
elif tab=="🏆 Awards":
    st.subheader("Season Awards")
    df = league.standings()
    if df.empty: st.write("No season data yet.")
    else:
        mvp=df.iloc[0]
        st.write(f"🏅 MVP: {mvp['Emoji']} {mvp['Name']} ({mvp['Grade']})")
        # Most Improved placeholder
        if league.season>1:
            improved=df.iloc[1]
            st.write(f"🌟 Most Improved: {improved['Emoji']} {improved['Name']}")
        # All Clash Team
        st.write("🔥 All Clash Team (Top 10)")
        for i,row in df.head(10).iterrows():
            st.write(f"{row['Emoji']} {row['Name']} ({row['Grade']})")

# --------------------------
# Playoffs Tab
# --------------------------
elif tab=="⚔️ Playoffs":
    st.subheader("Playoffs Bracket")
    champion,results=league.run_playoffs()
    if results is None:
        st.write("Playoffs not yet run. Simulate season first.")
    else:
        for rnd,res in results.items():
            st.write(f"### {rnd}")
            for match in res:
                st.write(f"{match['Match']} -> Winner: {match['Winner']}")
        st.success(f"🏆 Champion: {champion}")

# --------------------------
# Calendar Tab
# --------------------------
elif tab=="📅 Calendar":
    st.subheader("Season Calendar")
    cal_df=pd.DataFrame(league.calendar)
    cal_df["Date"]=cal_df["Date"].astype(str)
    st.dataframe(cal_df)

# --------------------------
# Balance Changes Tab
# --------------------------
elif tab=="🛠 Balance Changes":
    st.subheader("Balance Changes")
    st.write(f"Edit up to {MAX_BALANCE_CHANGE} cards per season:")
    editable_cards=random.sample(league.cards, min(MAX_BALANCE_CHANGE,len(league.cards)))
    changes=[]
    for c in editable_cards:
        st.write(f"{c.emoji()} {c.name}")
        atk=st.number_input(f"AtkDmg {c.name}", value=c.atk_dmg)
        hp=st.number_input(f"HP {c.name}", value=c.health)
        c.buff_nerf="B" if atk>c.atk_dmg or hp>c.health else "N"
        c.atk_dmg=atk
        c.health=hp
        changes.append(c.name)
    if st.button("Confirm Balance Changes"):
        st.success(f"Balance changes applied for cards: {', '.join(changes)}")
        league.balance_changes_done=True

# --------------------------
# League History Tab
# --------------------------
elif tab=="📜 League History":
    st.subheader("League History & Records")
    records=[]
    for c in league.cards:
        records.append({"Card":c.name,"Championships":c.championships,
                        "Wins":c.record["wins"],"Losses":c.record["losses"]})
    df=pd.DataFrame(records).sort_values(by="Wins",ascending=False)
    st.dataframe(df)

# --------------------------
# Save/Load Tab
# --------------------------
elif tab=="💾 Save/Load":
    st.subheader("Save / Load League State")
    if st.button("Save League"):
        data={"season":league.season,
              "cards":[vars(c) for c in league.cards],
              "calendar":league.calendar,
              "history":league.history}
        with open(SAVE_FILE,"w") as f: json.dump(data,f,default=str)
        st.success("League saved successfully.")
    if st.button("Load League"):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE,"r") as f: data=json.load(f)
            league.season=data["season"]
            for i,cdata in enumerate(data["cards"]):
                for k,v in cdata.items(): setattr(league.cards[i],k,v)
            league.calendar=data["calendar"]
            league.history=data["history"]
            st.success("League loaded successfully.")
        else: st.warning("No save file found.")

# --------------------------
# End of App
# --------------------------
