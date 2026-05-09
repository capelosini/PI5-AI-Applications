from game import Game

game = Game()
game.start()

print(game.state)
print(game.formatBoard(game.state["board"]))
