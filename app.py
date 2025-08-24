# Clash Royale – Minimal Stats & Balance (Streamlit)
# ------------------------------------------------
# Features:
# - Card Stats (sortable table)
# - Balance Changes editor (user customizable stats)
# - Balance Change History (auditable log)
# - Simulate Season (games + standings)
# - Top 10 cards each season
# - Up/Down arrows showing OVR movement vs. previous season
# ------------------------------------------------

import streamlit as st
import pandas as pd
import random
import json
import os
from dataclasses import dataclass, asdict, field

# --------------------------
# Config & Constants
# --------------------------
SEASON_GAMES = 82
SAVE_FILE = "cr_min_league_state.json"

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

EMOJI_FALLBACK = "🃏"
CARD_EMOJI_OVERRIDES = {
    "Hog Rider":"🐗","P.E.K.K.A":"🤖","Golden Knight":"🛡️","Electro Wizard":"⚡","Ice Spirit":"❄️",
    "Fireball":"🔥","Arrows":"🏹","Bats":"🦇","Goblin Gang":"👹","Prince":"🐴"
}

# --------------------------
# Helpers
# --------------------------

def card_emoji(name: str) -> str:
    return CARD_EMOJI_OVERRIDES.get(name, EMOJI_FALLBACK)


def grade_from_ovr(ovr: float) -> str:
    if ovr >= 95: return "S+"
    if ovr >= 90: return "S"
    if ovr >= 85: return "A"
    if ovr >= 80: return "B"
    if ovr >= 75: return "C"
    if ovr >= 70: return "D"
    return "E"


def trend_arrow(delta: float) -> str:
    if delta > 0.05: return "▲"
    if delta < -0.05: return "▼"
    return "↔"

# --------------------------
# Data Model
# --------------------------
@dataclass
class Card:
    name: str
    atk_dmg: int
    atk_speed: float
    health: int
    range: int
    atk_type: str
    card_speed: str
    buff_nerf: str = ""
    wins: int = 0
    losses: int = 0

    def ovr(self) -> float:
        type_val = 1 if "Melee" in self.atk_type else 2
        speed_val = {"Very Slow":1,"Slow":2,"Medium":3,"Fast":4,"Very Fast":5}[self.card_speed]
        raw_score = (
            0.19 * self.atk_dmg +
            0.11 * self.atk_speed * 100 +
            0.07 * self.range * 100 +
            0.22 * self.health / 10 +
            0.09 * type_val * 50 +
            0.16 * speed_val * 100
        )
        ovr_score = (raw_score / 2000) * 40 + 60
        return round(min(100, max(60, ovr_score)), 2)

    def record_game(self, win: bool):
        if win: self.wins += 1
        else: self.losses += 1


@dataclass
class League:
    season: int = 1
    cards: list = field(default_factory=list)
    prev_ovr: dict = field(default_factory=dict)  # name -> last season OVR
    season_history: list = field(default_factory=list)  # [{season, top10:[{name,ovr,grade}], games_played:int}]
    balance_history: list = field(default_factory=list) # [{season, card, old_stats, new_stats, delta_ovr}]

    def standings_df(self) -> pd.DataFrame:
        rows = []
        for c in self.cards:
            curr = c.ovr()
            last = self.prev_ovr.get(c.name, curr)
            delta = round(curr - last, 2)
            rows.append({
                "Emoji": card_emoji(c.name),
                "Card": c.name,
                "W": c.wins,
                "L": c.losses,
                "OVR": round(curr,2),
                "ΔOVR": delta,
                "Trend": trend_arrow(delta),
                "Grade": grade_from_ovr(curr),
                "ATK": c.atk_dmg,
                "ATK Spd": c.atk_speed,
                "HP": c.health,
                "Range": c.range,
                "Type": c.atk_type,
                "Speed": c.card_speed,
                "Buff/Nerf": c.buff_nerf or ""
            })
        df = pd.DataFrame(rows)
        return df.sort_values(["W","OVR"], ascending=[False, False]).reset_index(drop=True)

    def simulate_season(self, games_per_card: int = SEASON_GAMES):
        # reset wins/losses for fresh season sim
        for c in self.cards:
            c.wins = 0
            c.losses = 0

        # generate pairings for each round
        # each round: random shuffle then pair off
        rounds = games_per_card // 2  # each game uses 2 cards
        for _ in range(rounds):
            pool = self.cards.copy()
            random.shuffle(pool)
            for i in range(0, len(pool) - 1, 2):
                a, b = pool[i], pool[i+1]
                # simple win logic based on ovr + small randomness
                ovr_a, ovr_b = a.ovr(), b.ovr()
                bias = (ovr_a - ovr_b) / 40.0  # scale advantage
                r = random.random() + bias
                a_wins = r >= 0.5
                a.record_game(a_wins)
                b.record_game(not a_wins)

        # season summary
        df = self.standings_df()
        top10 = df.head(10)[["Card","OVR","Grade","W","L","Trend","ΔOVR"]].to_dict(orient="records")

        # update prev_ovr for next-season trend arrows
        for c in self.cards:
            self.prev_ovr[c.name] = c.ovr()

        self.season_history.append({
            "season": self.season,
            "top10": top10,
            "games_played": games_per_card
        })
        self.season += 1

    def apply_balance_changes(self, edited_df: pd.DataFrame):
        changes = 0
        for _, row in edited_df.iterrows():
            name = row["Card"]
            c = next((x for x in self.cards if x.name == name), None)
            if not c: continue

            # detect actual changes
            if (c.atk_dmg != row["ATK"] or c.atk_speed != row["ATK Spd"] or
                c.health != row["HP"] or c.range != row["Range"]):
                old_stats = {"ATK": c.atk_dmg, "ATK Spd": c.atk_speed, "HP": c.health, "Range": c.range, "OVR": c.ovr()}
                c.atk_dmg = int(row["ATK"])             # coerce types
                c.atk_speed = float(row["ATK Spd"]) 
                c.health = int(row["HP"]) 
                c.range = int(row["Range"]) 
                c.buff_nerf = row.get("Buff/Nerf", "")
                new_stats = {"ATK": c.atk_dmg, "ATK Spd": c.atk_speed, "HP": c.health, "Range": c.range, "OVR": c.ovr()}
                delta = round(new_stats["OVR"] - old_stats["OVR"], 2)
                self.balance_history.append({
                    "season": self.season,
                    "card": c.name,
                    "old": old_stats,
                    "new": new_stats,
                    "delta_ovr": delta
                })
                changes += 1
        return changes

# --------------------------
# Initialization
# --------------------------
@st.cache_data
def default_cards():
    cards = []
    for name in CARD_NAMES:
        cards.append(Card(
            name=name,
            atk_dmg=random.randint(80, 1200),
            atk_speed=round(random.uniform(0.5, 3.0), 2),
            health=random.randint(900, 2500),
            range=random.randint(1, 10),
            atk_type=random.choice(["Ground Melee", "Air Melee", "Ground Ranged", "Air Ranged"]),
            card_speed=random.choice(["Very Slow", "Slow", "Medium", "Fast", "Very Fast"]),
        ))
    return cards

if "league" not in st.session_state:
    st.session_state.league = League(cards=default_cards())
lg: League = st.session_state.league

st.set_page_config(page_title="CR – Stats & Balance", layout="wide")
st.title("🏆 Clash Royale – Stats & Balance")

# --------------------------
# Sidebar Controls
# --------------------------
st.sidebar.header("Season Controls")
colA, colB = st.sidebar.columns(2)
with colA:
    games = st.number_input("Games per card", min_value=20, max_value=200, value=SEASON_GAMES, step=2)
with colB:
    if st.button("Simulate Season ▶", use_container_width=True):
        lg.simulate_season(games_per_card=int(games))
        st.sidebar.success("Season simulated. Top 10 updated in history.")

st.sidebar.markdown("---")
st.sidebar.header("Add Custom Card")
with st.sidebar.form("add_card_form"):
    new_name = st.text_input("Card Name")
    col1, col2 = st.columns(2)
    with col1:
        n_atk = st.number_input("ATK", 50, 2000, 500)
        n_hp = st.number_input("HP", 200, 4000, 1200)
        n_range = st.number_input("Range", 1, 12, 5)
    with col2:
        n_as = st.number_input("ATK Spd", 0.2, 5.0, 1.2, step=0.05)
        n_type = st.selectbox("Type", ["Ground Melee", "Air Melee", "Ground Ranged", "Air Ranged"]) 
        n_speed = st.selectbox("Speed", ["Very Slow", "Slow", "Medium", "Fast", "Very Fast"]) 
    submitted = st.form_submit_button("Add Card")
    if submitted and new_name.strip():
        if any(c.name.lower() == new_name.lower() for c in lg.cards):
            st.sidebar.warning("Card with that name already exists.")
        else:
            lg.cards.append(Card(new_name.strip(), int(n_atk), float(n_as), int(n_hp), int(n_range), n_type, n_speed))
            st.sidebar.success(f"Added card: {new_name}")

st.sidebar.markdown("---")
# Save/Load (optional but handy for persistence)
if st.sidebar.button("💾 Save"):
    data = {
        "season": lg.season,
        "prev_ovr": lg.prev_ovr,
        "cards": [asdict(c) for c in lg.cards],
        "season_history": lg.season_history,
        "balance_history": lg.balance_history,
    }
    with open(SAVE_FILE, "w") as f: json.dump(data, f)
    st.sidebar.success("Saved league state.")

if st.sidebar.button("📂 Load"):
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f: data = json.load(f)
        lg.season = data.get("season", 1)
        lg.prev_ovr = data.get("prev_ovr", {})
        lg.cards = [Card(**c) for c in data.get("cards", [])]
        lg.season_history = data.get("season_history", [])
        lg.balance_history = data.get("balance_history", [])
        st.sidebar.success("Loaded league state.")
    else:
        st.sidebar.warning("No save file found.")

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["📊 Card Stats", "🛠 Balance Changes", "📜 History & Top 10"])

# --- Card Stats Tab ---
with tab1:
    st.subheader("Card Stats (with OVR trend)")
    df_stats = lg.standings_df()
    st.dataframe(df_stats, use_container_width=True)

# --- Balance Changes Tab ---
with tab2:
    st.subheader("Balance Changes – Edit and Apply")

    # Build editable table snapshot
    rows = []
    for c in lg.cards:
        curr = c.ovr()
        last = lg.prev_ovr.get(c.name, curr)
        delta = round(curr - last, 2)
        rows.append({
            "Card": c.name,
            "ATK": c.atk_dmg,
            "ATK Δ": 0,
            "ATK Spd": c.atk_speed,
            "ATK Spd Δ": 0.0,
            "HP": c.health,
            "HP Δ": 0,
            "Range": c.range,
            "Range Δ": 0,
            "OVR (curr)": curr,
            "ΔOVR vs Prev": delta,
            "Trend": trend_arrow(delta),
            "Buff/Nerf": c.buff_nerf or ""
        })
    df_edit = pd.DataFrame(rows)

    edited = st.data_editor(df_edit, use_container_width=True, num_rows="dynamic")

    # Live deltas & preview new OVR
    for i, row in edited.iterrows():
        base = next(x for x in lg.cards if x.name == row["Card"])
        edited.at[i, "ATK Δ"] = int(row["ATK"]) - int(base.atk_dmg)
        edited.at[i, "ATK Spd Δ"] = round(float(row["ATK Spd"]) - float(base.atk_speed), 2)
        edited.at[i, "HP Δ"] = int(row["HP"]) - int(base.health)
        edited.at[i, "Range Δ"] = int(row["Range"]) - int(base.range)
        # Temp card to preview OVR
        tmp = Card(base.name, int(row["ATK"]), float(row["ATK Spd"]), int(row["HP"]), int(row["Range"]), base.atk_type, base.card_speed)
        edited.at[i, "OVR (curr)"] = base.ovr()
        new_ovr = tmp.ovr()
        edited.at[i, "ΔOVR vs Prev"] = round(new_ovr - lg.prev_ovr.get(base.name, base.ovr()), 2)
        edited.at[i, "Trend"] = trend_arrow(edited.at[i, "ΔOVR vs Prev"]) 

    if st.button("Apply Changes ✅"):
        changed = lg.apply_balance_changes(edited)
        st.success(f"Applied {changed} changes. Logged to Balance History.")

    st.caption("Green ▲ means OVR up vs. last season; Red ▼ means down; ↔ means unchanged.")

# --- History & Top 10 Tab ---
with tab3:
    st.subheader("Season Top 10")
    if not lg.season_history:
        st.info("No seasons simulated yet. Use the sidebar to run a season.")
    else:
        for season_pack in reversed(lg.season_history):
            st.markdown(f"**Season {season_pack['season']}** — Games per card: {season_pack['games_played']}")
            tdf = pd.DataFrame(season_pack["top10"])  # Card, OVR, Grade, W, L, Trend, ΔOVR
            st.dataframe(tdf, use_container_width=True)
            st.markdown("---")

    st.subheader("Balance Change History")
    if not lg.balance_history:
        st.info("No balance changes applied yet.")
    else:
        hist_rows = []
        for h in lg.balance_history:
            hist_rows.append({
                "Season": h["season"],
                "Card": h["card"],
                "Old OVR": h["old"]["OVR"],
                "New OVR": h["new"]["OVR"],
                "ΔOVR": h["delta_ovr"],
                "Old ATK": h["old"]["ATK"],
                "New ATK": h["new"]["ATK"],
                "Old Spd": h["old"]["ATK Spd"],
                "New Spd": h["new"]["ATK Spd"],
                "Old HP": h["old"]["HP"],
                "New HP": h["new"]["HP"],
                "Old Range": h["old"]["Range"],
                "New Range": h["new"]["Range"],
            })
        st.dataframe(pd.DataFrame(hist_rows).sort_values(["Season","Card"]).reset_index(drop=True), use_container_width=True)

# --------------------------
# End of App
# --------------------------
