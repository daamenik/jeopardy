# Jeopardy! Player for Command Line Interface
This is a program you can use to play and keep score for real Jeopardy! games, sourced from j-archive.com.

## Setup
Python 3 and Pip required.
1. Clone the repo
2. In the repo's folder, run `pip -i .\requirements.txt`
3. The cache is loaded with data from my games, because this is my repo and I can do whatever I want. If you want to clear the cache, delete everything from the `cache` directory. When you play your first game, all new files will be plaed there automatically.

## Usage
To play one specific Jeopardy! game, you'll need the gameId for it, found at the end of a given j-archive URL. Once you have that, you can run
```
python3 .\jeopardy.py -g [gameId]
```

To play through an entire season (the program will ask if you want to play the next game before sending you into it), run
```
python3 .\jeopardy.py -s [seasonNumber]
```
If you want to stop playing after a game is over, the program will give you an option to quit and you can start where you left off in the season next time you run this command.

In both of these modes, you can either play manually (selecting each clue yourself through a coordinate system) or on automode (the program will just take you through each category in order). The game should guide you through this pretty well once you start playing.