import requests, sys, webbrowser, bs4
from ast import literal_eval as make_tuple
from colorama import init as color_init, Fore, Back
from os import system

color_init(autoreset=True)

class Game:
	"""Representation of a Jeopardy! game board.

	Attributes:
		score: total points one would recieve if this were a real Jeopardy! game.
		categories[6]: list of categories for the current round
		clues[6][5]: 2D array of {"clue", "response"} dicts, with each row corresponding to a category
			and each column corresponding to the dollar amount of that clue.
		autoMode: bool that determines if player wants to step through the clues automatically, without
			even looking at the clue board.

		------------- STATE DATA -------------
		boardState[6][5]: Stores which questions have been answered or are unavailable
		cluesRemaining: number of clues unanswered in the round
		currentCtg: current category
		currentAmt: current $ amount

		------------- FORMATTING DATA -------------
		ctgSpacing: length of longest category name + 5
	"""
	score = 0
	boardState = [ [False] * 5 for _ in range(6)]
	cluesRemaining = 0
	autoMode = False

	def __init__(self, gameId):
		self.newGame(gameId)
		self.initBoard()

		system('clear')
		title = self.page.select('#game_title > h1')
		print(f"\n{title[0].getText()}\n")

		autoplay = input("Would you like to use autoplay? Y/N: ").lower()
		if autoplay == 'y':
			self.autoMode = True

	"""
	newGame(self, gameId)

	Retrieves and reads HTML data for game #{gameId}
	"""
	def newGame(self, gameId):
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
		html_clues = self.page.select(f"#{round} .clue_text")
		html_responses = self.page.select(f"#{round} td > div")
		for clue, correctResponse in zip(html_clues, html_responses):
			# clue gathering
			row = int(clue["id"][-3]) - 1 # category
			col = int(clue["id"][-1]) - 1 # dollar amount

			self.boardState[row][col] = True
			self.cluesRemaining += 1

			# response gathering
			toggleTuple = str(correctResponse.get('onmouseover'))[6:]

			self.clues[row][col] = {
				"clue": clue.getText(),
				"response": bs4.BeautifulSoup(make_tuple(toggleTuple)[2], features="html.parser").select('.correct_response')[0].getText()
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

		print("\nScore: ", end='')
		print(Back.WHITE + Fore.BLACK + f"{self.score}")

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
		# displaying clue
		print()
		print(f'{self.categories[ctg]} for ', end='')
		print(Back.GREEN + Fore.BLACK + f'${self.dollarAmounts[amt]}', end='')
		print(":")
		print(Fore.YELLOW + self.clues[ctg][amt]["clue"])
		print()

		correct_response = self.clues[ctg][amt]['response']

		# if in auto mode, show score
		if (self.autoMode):
			print("Score: ", end='')
			print(Back.WHITE + Fore.BLACK + f"{self.score}")

		# answer prompt
		answer = input("Type answer here or press enter to pass: ").lower()
		print()

		# interpreting response and updating score
		wrongAnswer = False
		passed = False

		# Pass
		if answer == '':
			print(f"Correct response: ", end='')
			print(Fore.YELLOW + f"{correct_response}")
			passed = True
		# Correct
		elif answer == correct_response.lower():
			print(Back.GREEN + Fore.BLACK + "Correct!")
			self.score += self.dollarAmounts[amt]
		# Incorrect
		else:
			wrongAnswer = True
			print("You fucking numbskull.\n")
			print(f"Correct response: ", end='')
			print(Fore.RED + f"{correct_response}")
			self.score -= self.dollarAmounts[amt]

		# logging board state
		self.boardState[ctg][amt] = False
		self.cluesRemaining -= 1
		print(f"Score: {self.score}\n")

		# did we make a judgement error?
		if wrongAnswer or passed:
			answer = input("Press enter to continue, or 'y'/';' if you actually got it right. ")
			if answer == 'y' or answer == ';':
				if wrongAnswer:
					self.score += 2 * self.dollarAmounts[amt]
				else:
					self.score += self.dollarAmounts[amt]
			
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

		system('clear')
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
		print("Score: ", end='')
		print(Back.WHITE + Fore.BLACK + f"{self.score}")

		wager = int(input("\nEnter your wager: "))

		# getting clue
		finalClue = self.page.select('.final_round .category > div')
		toggleTuple = make_tuple(str(finalClue[0].get('onmouseout'))[6:])
		print(Fore.YELLOW + f"\n{toggleTuple[2]}")

		# getting correct response
		toggleTuple = make_tuple(str(finalClue[0].get('onmouseover'))[6:])
		correct_response = bs4.BeautifulSoup(toggleTuple[2], features="html.parser").select('.correct_response')[0].getText()

		# answer prompt
		answer = input("\nType answer here: ").lower()
		print()

		# Correct
		if answer == correct_response.lower():
			print(Back.GREEN + Fore.BLACK + "Correct!")
			self.score += wager
		# Incorrect
		else:
			print("You fucking numbskull.\n")
			print(f"Correct response: ", end='')
			print(Fore.RED + f"{correct_response}")
			self.score -= wager

			answer = input("Press enter to continue, or 'y'/';' if you actually got it right. ")
			if answer == 'y' or answer == ';':
				self.score += 2 * wager

	"""
	printScores(self, round="Jeopardy", selector="jeopardy_round")

	Prints your score and the other players' scores after a round. Does not print others' scores til
	after Double Jeopardy.
	"""
	def printScores(self, round="Jeopardy", selector="jeopardy_round"):
		print(f"\nScore after {round} round: ", end='')
		print(Fore.GREEN + f"{self.score}")

		if (round != "Jeopardy"):
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
			system('clear')
			print("Welcome to the Jeopardy Round. Here is your board:\n")
			self.printBoard()
			input("Press enter to play.")

		promptFunc = self.autoPrompt if self.autoMode else self.prompt

		while(self.cluesRemaining > 0):
			system('clear')
			promptFunc()

		system('clear')
		input("You have finished the Jeopardy round. Press enter to continue on to Double Jeopardy.")
		self.initBoard("double_jeopardy_round")

		if (self.autoMode):
			system('clear')
			print("Welcome to the Double Jeopardy Round. Here is your board:\n")
			self.printBoard()
			input("Press enter to play.")

		while (self.cluesRemaining > 0):
			system('clear')
			promptFunc()

		self.printScores("Double Jeopardy", "double_jeopardy_round")

		print("Welcome to Final Jeopardy.\n")
		self.finalJeopardy()
		self.printScores("Final Jeopardy", "final_jeopardy_round")
		

# --------------------------------------------------------------------------------------------------------------------------------------------------------		

def main():
	if len(sys.argv) != 2:
		print('Usage: python3 jeopardy.py gameId')
		sys.exit()

	gameId = int(sys.argv[1])
	if gameId < 1:
		print('Game ID must positive')
		sys.exit()

	print('Loading your Jeopardy game...')
	game = Game(gameId)
	game.play()

	print("Oh boy, that was fun! Bye!")


if __name__ == '__main__':
	main()
