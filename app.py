import streamlit as st
from clashlg import League

# ------------------------------
# INITIALIZE LEAGUE
# ------------------------------
if 'league' not in st.session_state:
    st.session_state.league = League()

league = st.session_state.league

# ------------------------------
# STREAMLIT UI
# ------------------------------
st.title("Clash Fantasy League")

menu = ["Standings", "Team Info", "Card Info", "Simulate Game", "Season Summary", "Top Meta Cards"]
choice = st.sidebar.selectbox("Menu", menu)

# ------------------------------
# STANDINGS
# ------------------------------
if choice == "Standings":
    st.subheader("Team Win/Loss Records")
    for team in league.teams:
        st.write(f"{team.name} - Wins: {team.wins}, Losses: {team.losses}")

# ------------------------------
# TEAM INFO
# ------------------------------
elif choice == "Team Info":
    team_select = st.selectbox("Select Team", [t.name for t in league.teams])
    team = next(t for t in league.teams if t.name == team_select)
    st.write(f"Team: {team.name} | Color: {team.color}")
    for card in team.cards:
        st.write(f"Card: {card.name} | OVR: {card.ovr_power} | Grade: {card.grade} | Elixir: {card.elixir_current:.1f} | Contribution: {card.contribution_pct} | Clutch: {card.clutch_play}")

# ------------------------------
# CARD INFO
# ------------------------------
elif choice == "Card Info":
    all_cards = [c for t in league.teams for c in t.cards]
    card_select = st.selectbox("Select Card", [c.name for c in all_cards])
    card = next(c for c in all_cards if c.name == card_select)
    st.write(f"Card: {card.name}")
    st.write(f"Stats: {card.stats}")
    st.write(f"OVR Power: {card.ovr_power} | Grade: {card.grade} | Trend: {card.trend}")
    st.write(f"Elixir: {card.elixir_current:.1f}")
    st.write(f"Contribution: {card.contribution_pct}")
    st.write(f"Clutch Play: {card.clutch_play}")

# ------------------------------
# SIMULATE GAME
# ------------------------------
elif choice == "Simulate Game":
    team1_name = st.selectbox("Select Team 1", [t.name for t in league.teams])
    team2_name = st.selectbox("Select Team 2", [t.name for t in league.teams if t.name != team1_name])
    team1 = next(t for t in league.teams if t.name == team1_name)
    team2 = next(t for t in league.teams if t.name == team2_name)

    if st.button("Simulate Game"):
        score1, score2 = league.simulate_game(team1, team2)
        st.write(f"{team1.cards[0].name} Score: {score1}")
        st.write(f"{team2.cards[0].name} Score: {score2}")

# ------------------------------
# SEASON SUMMARY
# ------------------------------
elif choice == "Season Summary":
    st.subheader("Season Summary")
    summary = league.season_summary()
    for team_data in summary:
        st.write(f"{team_data['team']} - Wins: {team_data['wins']}, Losses: {team_data['losses']}")
        for c in team_data['cards']:
            st.write(f"   Card: {c[0]} | OVR: {c[1]} | Grade: {c[2]} | Elixir: {c[3]}")

    if st.button("Assign Awards"):
        league.assign_awards()
        st.write("Awards Assigned!")
        st.write(league.history['awards'][-1])

# ------------------------------
# TOP META CARDS
# ------------------------------
elif choice == "Top Meta Cards":
    st.subheader("Top 10 Cards by OVR Power")
    top_cards = league.top_meta_cards()
    for c in top_cards:
        st.write(f"{c.name} | OVR: {c.ovr_power} | Grade: {c.grade} | Contribution: {c.contribution_pct} | Elixir: {c.elixir_current:.1f}")
