# MTG Life Tracker

A real-time web app for tracking life totals, commander damage, and poison counters during Magic: The Gathering games. Perfect for Commander/EDH pods where you need to track multiple damage sources across multiple players.

## How It Works

Each game gets its own shareable lobby with a unique ID (randomly generated from MTG card names). Everyone in your game can join the same lobby and see real-time updates as life totals, commander damage, and poison counters change.

## Usage

### Starting a Game

1. Visit the home page
2. Click "Go to Lobby" to create a new lobby (or enter an existing lobby ID to join one)
3. Share the lobby URL with your playgroup
4. Everyone's devices will sync automatically

### Tracking Stats

- **Life totals**: Use the +1/+5 and -1/-5 buttons to adjust each player's life
- **Commander damage**: Track damage from each opponent's commander separately
- **Poison counters**: Track poison accumulation for each player
- **Player names**: Click any player name to customize it
- **Add/Remove players**: Use the buttons at the bottom to adjust the number of players
- **Reset**: Reset all stats back to starting values (40 life, 0 damage/poison)

All changes sync instantly across all devices in the same lobby.

## Features

- Real-time sync across all devices via WebSockets
- Supports 1-4+ players (add as many as needed)
- Lobbies automatically clean up after 1 hour of inactivity
- Shareable URLs with fun MTG card-based lobby names

## Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
python app.py
```

3. Open `http://localhost:5000` in your browser
