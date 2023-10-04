# Jeopardy! Player for Command Line Interface
This is a program you can use to play and keep score for real Jeopardy! games, sourced from j-archive.com.

## Setup
Python 3 and Pip required.
1. Clone the repo
2. In the repo's folder, run `pip install -r .\requirements.txt`
3. There's a `cache` folder included that allows you to keep track of the games you've played as well as your play stats, which will automatically be displayed after a play session. The cache is loaded with data from my games, because this is my repo and I can do whatever I want. If you're cloning this for the first time, delete everything from the `cache` directory. When you play your first game, all new files will be placed there automatically to keep track of your games played and your stats.

## Usage
To play one specific Jeopardy! game, you'll need the gameId for it, found at the end of a given j-archive URL. Once you have that, you can run
```
python3 .\jeopardy.py -g [gameId]
```

To start playing or continue to play through an entire season (the program will ask if you want to play the next game before sending you into it), run
```
python3 .\jeopardy.py -s [seasonNumber]
```
If you want to stop playing after a game is over, the program will give you an option to quit and you can start where you left off in the season next time you run this command.

In both of these modes, you can either play manually (selecting each clue yourself through a coordinate system) or on automode (the program will just take you through each category in order). The game should guide you through this pretty well once you start playing.