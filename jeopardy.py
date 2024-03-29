import requests, sys, webbrowser, bs4
from ast import literal_eval as make_tuple
from colorama import init as color_init, Fore, Back
from os import system
from pathlib import Path
import pandas as pd
import csv
import argparse
import string

color_init(autoreset=True)

class Stats:
	"""Contains and updates stats for your overall Jeopardy performance

	Attributes:
		- numCorrectResponses: array that holds the number of correct J! and DJ! responses for each game
		- numCorrectDailyDoubles: array that holds the number of Daily Doubles answered correctly each game
		- finalJeopardyCorrect: array of bools that reflect whether or not you got the FJ! correct each game
		- currentGameComplete: used in the self.aggregate() function. If this is false, it will not count the data
			from the incomplete game.

	Methods:
		- initForNewGame(self)
		- addCorrectResponse(self, isDailyDouble=False)
		- addCorrectFinalJeopardy(self)
		- aggregate(self)
		- Destructor

	"""
	numCorrectResponses = []
	numCorrectDailyDoubles = []
	finalJeopardyCorrect = []
	currentGameComplete = False

	# adds new data to the stat arrays
	def initForNewGame(self):
		self.numCorrectResponses.append(0)
		self.numCorrectDailyDoubles.append(0)
		self.finalJeopardyCorrect.append(False)
		self.currentGameComplete = False
	
	# adds correct response (or correct Daily Double response)
	def addCorrectResponse(self, isDailyDouble=False):
		self.numCorrectResponses[-1] += 1
		if isDailyDouble:
			self.numCorrectDailyDoubles[-1] += 1

	# adds correct FJ! response
	def addCorrectFinalJeopardy(self):
		self.finalJeopardyCorrect[-1] = True

	"""
	aggregate(self)

	Responsible for creating and updating stats in the store. Creates stats.csv file if it doesn't
	exist, and uses data within it and within the class' attribute arrays to aggregate overall performance
	data. Fired upon class' destruction. Does not count stats from incomplete games.
	"""
	def aggregate(self):
		# if game is not complete, don't count the current scores
		if not self.currentGameComplete:
			self.numCorrectResponses = self.numCorrectResponses[:-1]

			# if above array is empty, that means only one game was played and incomplete,
			# therefore we don't bother with any calculation
			if self.numCorrectResponses == []:
				return

			self.numCorrectDailyDoubles = self.numCorrectDailyDoubles[:-1]
			self.finalJeopardyCorrect = self.finalJeopardyCorrect[:-1]

		# updating stats in cache
		statsPath = Path('.', 'cache', 'stats.csv')
		if statsPath.exists():
			statsDF = pd.read_csv(statsPath)
		else:
			# create stats data frame
			d = {
				'GamesPlayed': [0],
		        'CorrectResponseTotal': [0],
		        'CorrectDailyDoubleTotal': [0],
		        'CorrectFinalJeopardyTotal': [0],
		        'AvgCorrectResponses': [0.0],
		        'AvgCorrectResponsePct': [0.0],
		        'CorrectDailyDoublePct': [0.0],
		        'CorrectFinalJeopardyPct': [0.0]
		    }
			statsDF = pd.DataFrame(data=d)

		# game total
		gamesPlayed = statsDF.at[0, "GamesPlayed"] + len(self.numCorrectResponses)
		statsDF.at[0, "GamesPlayed"] = gamesPlayed

		# correct responses
		correctResponseTotal = sum(self.numCorrectResponses)
		statsDF.at[0, "CorrectResponseTotal"] = statsDF.at[0, "CorrectResponseTotal"] + correctResponseTotal
		correctResponseAvg = statsDF.at[0, "CorrectResponseTotal"] / gamesPlayed
		correctResponseAvgPct = correctResponseAvg / 60 # number of clues in standard game

		statsDF.at[0, "AvgCorrectResponses"] = correctResponseAvg
		statsDF.at[0, "AvgCorrectResponsePct"] = correctResponseAvgPct

		# daily doubles
		correctDailyDoubleTotal = sum(self.numCorrectDailyDoubles) + statsDF.at[0, "CorrectDailyDoubleTotal"]
		correctDailyDoublePct = correctDailyDoubleTotal / (3 * gamesPlayed) # three daily doubles per standard game
		statsDF.at[0, "CorrectDailyDoubleTotal"] = correctDailyDoubleTotal
		statsDF.at[0, "CorrectDailyDoublePct"] = correctDailyDoublePct

		# final jeopardy
		correctFinalJeopardyTotal = sum(self.finalJeopardyCorrect) + statsDF.at[0, "CorrectFinalJeopardyTotal"]
		correctFinalJeopardyPct = correctFinalJeopardyTotal / gamesPlayed # one FJ per standard game
		statsDF.at[0, "CorrectFinalJeopardyTotal"] = correctFinalJeopardyTotal
		statsDF.at[0, "CorrectFinalJeopardyPct"] = correctFinalJeopardyPct

		print(statsDF[['GamesPlayed', 'AvgCorrectResponses', 'AvgCorrectResponsePct', 'CorrectDailyDoublePct', 'CorrectFinalJeopardyPct']])
		statsDF.to_csv(statsPath, index=False)

	# destructor
	def __del__(self):
		self.aggregate()


class Game:
	"""Representation of a Jeopardy! game board.

	Attributes:
		- score: total points one would recieve if this were a real Jeopardy! game.
		- categories[6]: list of categories for the current round
		- clues[6][5]: 2D array of {"clue", "response"} dicts, with each row corresponding to a category
			and each column corresponding to the dollar amount of that clue.
		- autoMode: bool that determines if player wants to step through the clues automatically, without
			even looking at the clue board.
		- dailyDoubleCoords: [row, col] of daily double
		- title: Show number and date of game

		------------- STATE DATA -------------
		- boardState[6][5]: Stores which questions have been answered or are unavailable (denoted by bool)
		- cluesRemaining: number of clues unanswered in the round
		- currentCtg: current category (auto mode)
		- currentAmt: current $ amount (auto mode)

		------------- FORMATTING DATA -------------
		- ctgSpacing: length of longest category name + 1

	Methods:
		- __init__(self, gameId)
		- printScore(self)
		- newGame(self, gameId)
		- initBoard(self, round)
		- printBoard(self)
		- stepToNextClue(self)
		- giveClue(self, ctg, amt)
		- prompt(self)
		- autoPrompt(self)
		- finalJeopardy(self)
		- printScores(self, round="Jeopardy", selector="jeopardy_round")
		- play(self)
	"""
	autoMode = False

	def __init__(self, gameId):
		self.stats = Stats()
		self.newGame(gameId)

		autoplay = input("Would you like to use autoplay? Y/N: ").lower()
		if autoplay == 'y':
			self.autoMode = True

	def printScore(self):
		print("Score: ", end='')
		print(Back.WHITE + Fore.BLACK + f"{self.score}")

	"""
	newGame(self, gameId)

	Retrieves and reads HTML data for game #{gameId}
	"""
	def newGame(self, gameId):
		# reset member vars
		self.score = 0
		self.boardState = [ [False] * 5 for _ in range(6)]
		self.cluesRemaining = 0
		self.dailyDoubleCoords = [6, 6]

		self.gameId = gameId

		# loading categories
		res = requests.get(f"http://www.j-archive.com/showgame.php?game_id={gameId}")
		res.raise_for_status()
		self.page = bs4.BeautifulSoup(res.text, features="html.parser")

		# check if game exists
		error = self.page.select('#content .error')
		if (error):
			print("Game does not exist.")
			sys.exit()

		# initialize board/stats and print game info
		system('cls||clear')
		self.title = self.page.select('#game_title > h1')
		print(f"\n{self.title[0].getText()}\n")

		self.initBoard()
		self.stats.initForNewGame()

	"""
	initBoard(self, round)
		round is in ["jeopardy_round", "double_jeopardy_round"]

	Initializes the categories, dollar amounts, and clues for the specified {round}.
	"""
	def initBoard(self, round="jeopardy_round"):
		self.cluesRemaining = 0
		self.currentCtg = self.currentAmt = 0

		# setting dollar amounts
		if round == "double_jeopardy_round":
			self.dollarAmounts = [400, 800, 1200, 1600, 2000]
		else:
			round = "jeopardy_round" # default
			self.dollarAmounts = [200, 400, 600, 800, 1000]
		
		# loading categories
		html_categories = self.page.select(f'#{round} .category_name')
		self.categories = [c.getText() for c in html_categories]
		self.ctgSpacing = max([len(c) for c in self.categories]) + 1

		# loading clues
		self.clues = [[{} for _ in range(5)] for _ in range(6)]

		# populating board with clues
		html_clues_and_responses = self.page.select(f"#{round} .clue_text")

		html_clues = []
		html_responses = []
		for clue in html_clues_and_responses:
			if (clue['id'][-1] == 'r'):
				html_responses.append(clue.find(class_="correct_response"))
			else:
				html_clues.append(clue)

		html_dd_info = self.page.select(f"#{round} td > div")
		for clue, correctResponse, info in zip(html_clues, html_responses, html_dd_info):
			# clue gathering
			row = int(clue["id"][-3]) - 1 # category
			col = int(clue["id"][-1]) - 1 # dollar amount

			self.boardState[row][col] = True
			self.cluesRemaining += 1

			# is this the Daily Double?
			if info.find(class_="clue_value_daily_double"):
				self.dailyDoubleCoords = [row, col]

			self.clues[row][col] = {
				"clue": clue.getText(),
				"response": correctResponse.getText()
			}

	"""
	printBoard(self)

	Prints the categories and current clues available for the round.
	"""
	def printBoard(self):
		# column headers
		print("{:>{width}}[1]    [2]    [3]    [4]    [5]".format(" ", width=(self.ctgSpacing + 7)))

		rowNum = 0
		for category in self.categories:
			print("[{}] {:>{width}}   ".format(rowNum + 1, category, width=self.ctgSpacing), end='')

			# print $ amounts
			for i in range(5):
				if self.boardState[rowNum][i]:
					print("${:<6}".format(self.dollarAmounts[i]), end='')
				else:
					print("---    ", end='')

			print()
			rowNum += 1

		print()
		self.printScore()

	"""
	stepToNextClue(self)

	Advances to the next clue in the category. If none are left, advances
	to the next category.
	"""
	def stepToNextClue(self):
		if (self.cluesRemaining <= 0):
			return

		while (not self.boardState[self.currentCtg][self.currentAmt]):
			if self.currentAmt == 4: # end of the category
				self.currentAmt = 0
				self.currentCtg += 1
			else:
				self.currentAmt += 1


	"""
	giveClue(self, ctg, amt)

	Displays the clue in {ctg} for {amt}. Lets user input an answer, interprets it, and updates
	their score.
	"""
	def giveClue(self, ctg, amt):
		points = self.dollarAmounts[amt]
		isDailyDouble = False

		# displaying clue
		print()
		print(f'[{ctg + 1}] {self.categories[ctg]} for ', end='')
		print(Back.GREEN + Fore.BLACK + f'${self.dollarAmounts[amt]}', end='')
		print(":")

		# Daily Double logic
		if [ctg, amt] == self.dailyDoubleCoords:
			isDailyDouble = True
			self.printScore()
			print(Back.LIGHTMAGENTA_EX + "\nDaily Double! Enter wager:", end='')
			points = int(input(" "))
			
			# getting valid point value
			validPointMax = 1000 if self.score < 1000 else self.score
			while (points > validPointMax):
				points = int(input(f"Please enter a value up to ${validPointMax}: "))

			print()

		# print clue
		print(Fore.YELLOW + self.clues[ctg][amt]["clue"])
		print()

		# if in auto mode, show score
		if (self.autoMode):
			self.printScore()

		correctResponseOriginal = self.clues[ctg][amt]['response']
		correctResponse = self.standardizeResponse(correctResponseOriginal)

		# answer prompt
		answer = input("Type answer here or press enter to pass: ").lower()
		print()
		answer = self.standardizeResponse(answer) if answer != '' else answer

		# interpreting response and updating score
		wrongAnswer = False
		passed = False

		# Pass
		if answer == '':
			print(f"Correct response: ", end='')
			print(Fore.YELLOW + f"{correctResponseOriginal}")
			passed = True

			if isDailyDouble:
				self.score -= points
				wrongAnswer = True
		# Correct
		elif answer == correctResponse:
			print(Back.GREEN + Fore.BLACK + "Correct!")
			self.score += points
			
			self.stats.addCorrectResponse(isDailyDouble)
		# Incorrect
		else:
			wrongAnswer = True
			print(f"Correct response: ", end='')
			print(Fore.RED + f"{correctResponseOriginal}")
			self.score -= points

		# logging board state
		self.boardState[ctg][amt] = False
		self.cluesRemaining -= 1
		print(f"Score: {self.score}\n")

		# did we make a judgement error?
		if wrongAnswer or passed:
			answer = input("Press enter to continue, or another key and then enter if you actually got it right. ")
			if answer != '':
				if wrongAnswer:
					self.score += 2 * points
				else:
					self.score += points

				self.stats.addCorrectResponse(isDailyDouble)
			
			return
		
		input("Press enter to continue.")

	"""
	prompt(self)

	Contains most of the gameplpay logic. Prints the board, lets the user pick a clue, displays the clue, 
	and lets them answer. Also interprets the answer and updates the score accordingly.
	"""
	def prompt(self):
		self.printBoard()
		print()
		clueInput = input("Enter a clue coordinate (e.g., 14) or press enter to automatically move on to the next clue: ")

		ctg = amt = 0
		if clueInput == '': # auto-continue
			self.stepToNextClue()

			ctg = self.currentCtg
			amt = self.currentAmt
		else: # coordinates input
			while True:
				coords = int(clueInput)
				ctg = (coords // 10) - 1
				amt = (coords % 10) - 1

				if (ctg < 0) or (ctg > 5) or (amt < 0) or (amt > 4):
					clueInput = input("Invalid coordinates, try again: ")
				elif not self.boardState[ctg][amt]:
					clueInput = input("Clue unavailable, try again: ")
				else: # valid clue
					break

		system('cls||clear')
		self.giveClue(ctg, amt)

	def autoPrompt(self):
		self.stepToNextClue()
		self.giveClue(self.currentCtg, self.currentAmt)

	"""
	finalJeopardy(self)

	Plays through the Final Jeopardy round
	"""
	def finalJeopardy(self):
		# displaying category
		category = self.page.select('.final_round .category_name')
		print(f"Category: {category[0].getText()}")
		self.printScore()

		wager = 0
		wagerAnswer = input("\nEnter your wager: ")
		if wagerAnswer != "":
			wager = int(wagerAnswer)

		# getting clue
		finalClue = self.page.select('#clue_FJ')[0].getText()
		print(Fore.YELLOW + f"\n{finalClue}")

		# getting correct response
		correct_response = self.page.select("#clue_FJ_r .correct_response")[0].getText()

		# answer prompt
		answer = input("\nType answer here: ").lower()
		print()

		# Correct
		if answer == correct_response.lower():
			print(Back.GREEN + Fore.BLACK + "Correct!")
			self.score += wager
			self.stats.addCorrectFinalJeopardy()
		# Incorrect
		else:
			print(f"Correct response: ", end='')
			print(Fore.RED + f"{correct_response}")
			self.score -= wager

			answer = input("Press enter to continue, or another key if you actually got it right. ")
			if answer != '':
				self.score += 2 * wager
				self.stats.addCorrectFinalJeopardy()

	"""
	printScores(self, round="Jeopardy", selector="jeopardy_round")

	Prints your score and the other players' scores after a round. Does not print others' scores til
	after Double Jeopardy.
	"""
	def printScores(self, round="Jeopardy", selector="jeopardy_round"):
		print(f"\nScore after {round} round: ", end='')
		print(Fore.GREEN + f"{self.score}")

		scores = self.page.find(id=selector).find_all(class_=["score_positive", "score_negative"])
		print(f"Other scores: ", end='')
		for score in scores[:3]:
			print(f"{score.getText()} ", end='')
		print()
		
		input("Press enter to continue.")

	"""
	play(self)

	This takes us through the game. It goes through the jeopardy round until there are no clues left,
	then goes through the double jeopardy round, then to final jeopardy.
	"""
	def play(self):
		if self.autoMode:
			system('cls||clear')
			print(f"\n{self.title[0].getText()}\n")
			print("Welcome to the Jeopardy Round. Here is your board:\n")
			self.printBoard()
			input("Press enter to play.")

		promptFunc = self.autoPrompt if self.autoMode else self.prompt

		while(self.cluesRemaining > 0):
			system('cls||clear')
			promptFunc()

		system('cls||clear')
		self.printScores()
		self.initBoard("double_jeopardy_round")

		if (self.autoMode):
			system('cls||clear')
			print(f"\n{self.title[0].getText()}\n")
			print("Welcome to the Double Jeopardy Round. Here is your board:\n")
			self.printBoard()
			input("Press enter to play.")

		while (self.cluesRemaining > 0):
			system('cls||clear')
			promptFunc()

		self.printScores("Double Jeopardy", "double_jeopardy_round")

		print("Welcome to Final Jeopardy.\n")
		self.finalJeopardy()
		self.stats.currentGameComplete = True
		self.printScores("Final Jeopardy", "final_jeopardy_round")
		
	"""
	standardizeResponse(self, originalResponse)
		returns stdResponse (string)

	transform current response to minimize small, trivial differences from user input:
		- make lowercase
		- strip all punctuation
		- remove leading articles (a and an)
		- change "&" to "and"
	"""
	def standardizeResponse(self, originalResponse):
		stdResponse = originalResponse.lower()
		stdResponse = stdResponse.replace("&", "and")
		stdResponse = stdResponse.translate(str.maketrans('', '', string.punctuation))

		if stdResponse == '':
			return stdResponse

		if stdResponse[0] == 'a' or stdResponse[0] == 't':
			firstWord = stdResponse.split(' ')[0]
			if firstWord == 'a':
				stdResponse = stdResponse[2:]
			elif firstWord == 'an' or firstWord == 'to':
				stdResponse = stdResponse[3:]
			elif firstWord == 'the':
				stdResponse = stdResponse[4:]
		
		return stdResponse

# --------------------------------------------------------------------------------------------------------------------------------------------------------

class GameLog:
	gameIds = []
	idIndex = 0
	season = 0
	seasonCachePath = ""

	def __init__(self, season):
		if season < 1 or season > 40:
			print("There are only 40 seasons of Jeopardy available.")
			sys.exit()

		self.season = season

		gameLogCachePath = Path('.', 'cache', 'gamelog.csv')
		if not gameLogCachePath.exists():
			with open(gameLogCachePath, 'w') as gameLog:
				for i in range(39):
					gameLog.write("0\n")

		# read file with season/game mapping
		self.df = pd.read_csv(gameLogCachePath, header=None)
		self.idIndex = self.df.iat[season - 1, 0]
		self.seasonCachePath = Path('.', 'cache', f"{season}.csv")

		if (self.seasonCachePath.exists()):
			self.readGameIdsFromCache()
		else:
			self.scrapeGameIdsForSeason()

	"""
	__del__(self)

	Destructor. Updates the gamelog.
	"""
	def __del__(self):
		self.df.to_csv(Path('.', 'cache', 'gamelog.csv'), index=False, header=False)

	"""
	scrapeGameIdsForSeason(self)

	Given a season, scrapes the game IDs for that season and places them into the cache
	in a file called {self.season}.csv, as well as this object's self.gameIds array
	"""
	def scrapeGameIdsForSeason(self):
		# read in season page
		res = requests.get(f"https://j-archive.com/showseason.php?season={self.season}")
		res.raise_for_status()
		currentSeasonPage = bs4.BeautifulSoup(res.text, features="html.parser")

		# get game ids
		self.gameIds = [int(a.get('href').split('=')[1]) for a in currentSeasonPage.table.find_all('a')]
		self.gameIds.reverse()

		# write game IDs to cache
		with open(self.seasonCachePath, 'w') as cache:
			for id in self.gameIds[:-1]:
				cache.write(f"{id},")
			cache.write(f"{self.gameIds[-1]}")


	def readGameIdsFromCache(self):
		with open(self.seasonCachePath, newline='') as cache:
			reader = csv.reader(cache)
			self.gameIds = [int(id) for id in list(reader)[0]]

	def getCurrentGameId(self):
		# have we reached the end of the season?
		if self.idIndex == len(self.gameIds):
			self.df.iat[self.season - 1, 0] = 0
			print("END OF SEASON REACHED.")
			sys.exit()

		id = self.gameIds[self.idIndex]
		self.idIndex += 1
		self.df.iat[self.season - 1, 0] = self.idIndex

		self.df.to_csv(Path('.', 'cache', 'gamelog.csv'), index=False, header=False)

		return id

	"""
	getNextGameId(self)

	Gets the next game ID in the current season you're playing through. If you've reached the end,
	it tells you and resets your progress in the season to zero.
	"""
	def getNextGameId(self):
		self.idIndex += 1
		if self.idIndex > len(self.gameIds):
			self.df.iat[self.season - 1, 0] = 0
			print("END OF SEASON REACHED.")
			sys.exit()

		self.df.iat[self.season - 1, 0] = self.idIndex
		return self.getCurrentGameId()

	


# --------------------------------------------------------------------------------------------------------------------------------------------------------

def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('-s', '--season', help='Season you would like to start or continue playing through.')
	parser.add_argument('-g', '--game', metavar='gameID', help='ID of specific game you would like to play.')

	args = parser.parse_args()

	# play through season
	if args.season:
		print("Loading season data...")
		gl = GameLog(int(args.season))
		gameId = gl.getCurrentGameId()

		print("Loading your Jeopardy game...")
		game = Game(gameId)
		game.play()

		# do we want to keep playing?
		keepPlaying = input("Play next game in season? Y/N: ").lower()
		while keepPlaying == 'y':
			gameId = gl.getCurrentGameId()

			print("Loading your Jeopardy game...")
			game.newGame(gameId)
			game.play()
			keepPlaying = input("Play next game in season? Y/N: ").lower()


	# play one game only
	elif args.game:
		gameId = int(args.game)
		if gameId < 1:
			print('Game ID must positive')
			sys.exit()
		
		print("Loading your Jeopardy game...")
		game = Game(gameId)
		game.play()

	print("\nOh boy, that was fun! Bye!")


if __name__ == '__main__':
	main()
