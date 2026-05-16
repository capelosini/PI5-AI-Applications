import random

import torch
from game import ACTIONS_COMBINED, BOARD_SIZE, TEAM_ID, Game  # Import your classes
from model import Model, device


def play_test_match(model_path):

    game = Game()
    game.start()

    model = Model(
        board_size=BOARD_SIZE, actions_n=len(ACTIONS_COMBINED) * len(TEAM_ID)
    ).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()  # Set to evaluation mode (turns off Dropout/BatchNorm)

    print("Match Started: AI (Turing) vs Random Bot (Lovelace)")

    turn_count = 0
    while game.status == "PLAYING":
        game.render()
        turn_count += 1
        current_team = TEAM_ID[game.turn_team_id]
        mask = game.get_valid_mask()
        valid_indices = torch.where(mask)[0]

        # Check for Stalemate
        if len(valid_indices) == 0:
            game.status = "FINISHED"
            game.winner = TEAM_ID[3 - game.turn_team_id]
            print(f"Stalemate! {current_team} has no moves.")
            break

        if current_team == "turing":
            # --- AI PLAYER ---
            state_tensor = game.get_state_tensor().unsqueeze(0).to(device)
            with torch.no_grad():
                q_values = model(state_tensor)
                q_values[0][~mask] = -1e9  # Mask illegal moves
                action = torch.argmax(q_values).item()
        else:
            # --- RANDOM BOT ---
            action = random.choice(valid_indices.tolist())

        game.apply_action(action)

    game.render()
    print(f"--- Results after {turn_count} turns ---")
    print(f"Winner: {game.winner}")
    if game.winner == "turing":
        print("Victory for the AI!")
    else:
        print("The AI lost to a random bot. Needs more training!")


if __name__ == "__main__":
    try:
        play_test_match("captcha_2.0_final.pth")
    except FileNotFoundError:
        print(
            "Error: captcha_2.0_final.pth not found. Please train and save the model first."
        )
