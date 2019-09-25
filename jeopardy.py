import requests, sys, webbrowser, bs4

if len(sys.argv) is not 2:
	print('Usage: python3 jeopardy.py gameId')
	sys.exit()

gameId = int(sys.argv[1])
if gameId < 1 or gameId > 6423:
	print('Game ID must be between 1 and 6423')
	sys.exit()

print('Loading your Jeopardy game...')

res = requests.get(f"http://www.j-archive.com/showgame.php?game_id={gameId}")
res.raise_for_status()

page = bs4.BeautifulSoup(res.text, features="html.parser")

categories = page.select('#jeopardy_round .category_name')
for c in categories:
	print(c.getText())

print("---------------------------------")
print("Correct Responses")

toggleLine = page.select('td > div')[0]
print(str(toggleLine.get('onmouseover')))
