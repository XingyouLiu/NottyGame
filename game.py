import pygame
import os
from typing import List, Tuple, Dict, Optional, Set
from player import Player
from collection_of_cards import CollectionOfCards
import random
from computer_player import ComputerPlayer, RandomStrategyPlayer, ExpectationValueStrategyPlayer


class GamePhase:
    SETUP = "setup"
    PLAYER_TURN = "player_turn"
    GAME_OVER = "game_over"


class Game:
    def __init__(self):
        pygame.init()
        self.width = 1600
        self.height = 900
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Notty Game")

        # Colours
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BACKGROUND_COLOR = (34, 139, 34)

        self.deck: List[Tuple[str, int]] = [(colour, number) for colour in {'red', 'blue', 'green', 'yellow'} for number
                                            in range(1, 11) for _ in range(2)]
        random.shuffle(self.deck)

        self.players: List[Player] = []
        self.game_phase = GamePhase.SETUP
        self.current_player = None
        self.selected_cards: List[int] = []
        self.turn_state = self.initial_turn_state()

        # button positions
        self.button_positions = {
            'draw': pygame.Rect(self.width - 150, self.height - 100, 120, 80),
            'take': pygame.Rect(self.width - 150, self.height - 180, 120, 80),
            'discard': pygame.Rect(self.width - 150, self.height - 260, 120, 80),
            'pass': pygame.Rect(self.width - 150, self.height - 340, 120, 80),
            'next': pygame.Rect(self.width - 150, self.height - 420, 120, 80)
        }

        # player to take card from - select buttons
        self.player_select_buttons = {}
        self.showing_player_select_buttons = False

        # card layout constants
        self.CARD_LEFT_MARGIN = 20
        self.CARD_SPACING = 65
        self.CARD_WIDTH = 60
        self.CARD_HEIGHT = 100

        self.load_assets()
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.message = ""
        self.current_turn_text = ""

        self.computer_buttons = {}
        self.selected_computers = []
        self.game_phase = GamePhase.SETUP

    def initial_turn_state(self):
        return {
            'action_taken': False,  # mark if the main action has been taken (Draw already 3 cards/Take/Pass)
            'has_drawn': False,  # mark if at least one card has been drawn
            'has_taken': False,  # mark if a card has been taken
            'cards_drawn': 0,  # record how many cards have been drawn in this turn
            'waiting_for_take': False  # mark if having clicked 'Take' button and waiting for selecting a card to take
        }

    def load_assets(self):
        self.card_images = {}
        for color in ['red', 'blue', 'green', 'yellow']:
            for number in range(1, 11):
                card_image = pygame.image.load(os.path.join('cards', f'{color}_{number}.png'))
                self.card_images[(color, number)] = pygame.transform.scale(card_image,
                                                                           (self.CARD_WIDTH, self.CARD_HEIGHT))

        background_image = pygame.image.load(os.path.join('backgrounds', 'gradient_background.png'))
        self.background = pygame.transform.scale(background_image, (self.width, self.height))

        self.buttons = {}
        for button_name in ['draw', 'take', 'discard', 'pass', 'next']:
            button_image = pygame.image.load(os.path.join('buttons', f'{button_name}_normal.png'))
            self.buttons[button_name] = pygame.transform.scale(button_image, (
            self.button_positions[button_name].width, self.button_positions[button_name].height))

    def game_screen(self):
        font = pygame.font.Font(None, 36)

        if self.current_player:
            turn_text = f"Current Turn: {self.current_player.name}"
            turn_surface = font.render(turn_text, True, self.BLACK)
            turn_rect = turn_surface.get_rect(centerx=self.width // 2, top=20)
            self.screen.blit(turn_surface, turn_rect)

        deck_text = font.render(f"Deck: {len(self.deck)} cards", True, self.BLACK)
        self.screen.blit(deck_text, (20, 20))

        for i, player in enumerate(self.players):
            self.display_player_hand(player, 100 + i * 150)

        if self.current_player and self.current_player.is_human:
            self.display_action_buttons()

        if self.selected_cards:
            self.highlight_human_valid_groups()

        self.display_valid_groups_panel()

        if self.message:
            messages = self.message.split('\n')
            for i, message_line in enumerate(messages):
                words = message_line.split()
                lines = []
                current_line = []
                current_length = 0
                for word in words:
                    if current_length + len(word) + 1 <= 80:
                        current_line.append(word)
                        current_length += len(word) + 1
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                if current_line:
                    lines.append(' '.join(current_line))

                for j, line in enumerate(lines):
                    message_text = font.render(line, True, self.BLACK)
                    self.screen.blit(message_text, (20, self.height - 150 + (i * len(lines) + j) * 30))

        if self.showing_player_select_buttons:
            self.display_player_select_buttons()

    def setup_screen(self):
        font = pygame.font.Font(None, 48)

        title = font.render("Welcome to Notty Game!", True, self.BLACK)
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title, title_rect)

        subtitle = font.render("Select 1-2 Computer Players:", True, self.BLACK)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 160))
        self.screen.blit(subtitle, subtitle_rect)

        available_computers = [
            ("Computer 1 (Random Strategy)", RandomStrategyPlayer("Computer 1")),
            ("Computer 2 (Random Strategy)", RandomStrategyPlayer("Computer 2")),
            ("Computer 3 (Calculating Expectation Strategy)", ExpectationValueStrategyPlayer("Computer 3")),
            ("Computer 4 (Calculating Expectation Strategy)", ExpectationValueStrategyPlayer("Computer 4"))
        ]

        button_height = 50
        button_spacing = 20
        for i, (name, computer_player) in enumerate(available_computers):
            button_rect = pygame.Rect(
                self.width // 2 - 150,
                220 + i * (button_height + button_spacing),
                300,
                button_height
            )

            is_selected = any(comp.name == computer_player.name for comp in self.selected_computers)

            if is_selected:
                pygame.draw.rect(self.screen, (200, 255, 200), button_rect)
            else:
                pygame.draw.rect(self.screen, self.WHITE, button_rect)

            pygame.draw.rect(self.screen, self.BLACK, button_rect, 2)
            text = font.render(name, True, self.BLACK)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)

            self.computer_buttons[name] = (button_rect, computer_player)

        if len(self.selected_computers) > 0:
            start_button = pygame.Rect(
                self.width // 2 - 100,
                220 + len(available_computers) * (button_height + button_spacing),
                200,
                button_height
            )
            pygame.draw.rect(self.screen, (150, 255, 150), start_button)
            pygame.draw.rect(self.screen, self.BLACK, start_button, 2)
            start_text = font.render("Start Game", True, self.BLACK)
            start_rect = start_text.get_rect(center=start_button.center)
            self.screen.blit(start_text, start_rect)
            self.computer_buttons['start'] = (start_button, None)

    def display_action_buttons(self):
        for action, rect in self.button_positions.items():
            self.screen.blit(self.buttons[action], rect)

    def display_player_hand(self, player: Player, y_position: int):
        font = pygame.font.Font(None, 36)
        text = font.render(f"{player.name}'s hand", True, self.BLACK)
        self.screen.blit(text, (self.CARD_LEFT_MARGIN, y_position - 30))

        for i, card in enumerate(player.hand):
            card_image = self.card_images[card]
            x = self.CARD_LEFT_MARGIN + i * self.CARD_SPACING

            card_rect = pygame.Rect(x, y_position, self.CARD_WIDTH, self.CARD_HEIGHT)

            if player == self.current_player and i in self.selected_cards:
                pygame.draw.rect(self.screen, self.GREEN, card_rect, 3)

            self.screen.blit(card_image, (x, y_position))

    def display_player_select_buttons(self):
        if not self.showing_player_select_buttons:
            return

        font = pygame.font.Font(None, 36)
        button_height = 50
        button_width = 200
        spacing = 20

        other_players = [p for p in self.players if p != self.current_player]
        for i, player in enumerate(other_players):
            button_rect = pygame.Rect(
                self.width - button_width - 20,
                200 + i * (button_height + spacing),
                button_width,
                button_height
            )
            self.player_select_buttons[player.name] = button_rect

            pygame.draw.rect(self.screen, self.WHITE, button_rect)
            text = font.render(f"Take from {player.name}", True, self.BLACK)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)

    def display_valid_groups_panel(self):
        if not self.current_player.exist_valid_group():
            return

        font = pygame.font.Font(None, 36)
        valid_groups = self.current_player.all_valid_groups_with_largest_length()

        panel_x = self.width - 500
        panel_y = self.height - 420

        title = "Current Valid Groups:"
        title_text = font.render(title, True, self.BLACK)
        self.screen.blit(title_text, (panel_x, panel_y))

        y_offset = 40
        for i, group in enumerate(valid_groups):
            group_desc = ', '.join(f"{card[0]} {card[1]}" for card in group)
            group_text = font.render(f"{i + 1}. {group_desc}", True, self.BLACK)
            self.screen.blit(group_text, (panel_x, panel_y + y_offset + i * 30))

    def show_game_over_popup(self, winner_name: str):
        popup_width = 400
        popup_height = 200
        popup_x = (self.width - popup_width) // 2
        popup_y = (self.height - popup_height) // 2

        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(self.screen, self.WHITE, popup_rect)
        pygame.draw.rect(self.screen, self.BLACK, popup_rect, 2)

        font = pygame.font.Font(None, 48)

        winner_text = f"{winner_name} wins!"
        text_surface = font.render(winner_text, True, self.BLACK)
        text_rect = text_surface.get_rect(centerx=self.width // 2, centery=self.height // 2 - 40)
        self.screen.blit(text_surface, text_rect)

        button_width = 120
        button_height = 40
        button_y = self.height // 2 + 20

        restart_button = pygame.Rect(self.width // 2 - button_width - 20, button_y, button_width, button_height)
        quit_button = pygame.Rect(self.width // 2 + 20, button_y, button_width, button_height)

        pygame.draw.rect(self.screen, (200, 200, 200), restart_button)
        pygame.draw.rect(self.screen, (200, 200, 200), quit_button)
        pygame.draw.rect(self.screen, self.BLACK, restart_button, 2)
        pygame.draw.rect(self.screen, self.BLACK, quit_button, 2)

        font = pygame.font.Font(None, 36)
        restart_text = font.render("Restart", True, self.BLACK)
        quit_text = font.render("Quit", True, self.BLACK)

        restart_text_rect = restart_text.get_rect(center=restart_button.center)
        quit_text_rect = quit_text.get_rect(center=quit_button.center)

        self.screen.blit(restart_text, restart_text_rect)
        self.screen.blit(quit_text, quit_text_rect)

        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if restart_button.collidepoint(mouse_pos):
                        new_game = Game()
                        new_game.run()
                        return
                    elif quit_button.collidepoint(mouse_pos):
                        pygame.quit()
                        exit()

    def click_on_setup(self, pos: Tuple[int, int]):
        for name, (rect, computer_player) in self.computer_buttons.items():
            if rect.collidepoint(pos):
                if name == 'start':
                    if len(self.selected_computers) > 0:
                        self.start_game(self.selected_computers)
                else:
                    is_selected = any(comp.name == computer_player.name for comp in self.selected_computers)

                    if is_selected:
                        self.selected_computers = [comp for comp in self.selected_computers
                                                   if comp.name != computer_player.name]
                    elif len(self.selected_computers) < 2:
                        self.selected_computers.append(computer_player)
                break

    def click_in_game(self, pos: Tuple[int, int]):
        if self.showing_player_select_buttons:
            for player_name, button_rect in self.player_select_buttons.items():
                if button_rect.collidepoint(pos):
                    target_player = None
                    for player in self.players:
                        if player.name == player_name:
                            target_player = player
                            break
                    self.human_take(target_player)
                    return

        for action, rect in self.button_positions.items():
            if rect.collidepoint(pos):
                if action == 'draw':
                    self.human_draw()
                elif action == 'take':
                    self.human_select_take()
                elif action == 'pass':
                    self.human_pass()
                elif action == 'discard':
                    self.human_discard()
                elif action == 'next':
                    self.human_start_next_turn()
                return

        self.click_card(pos)

    def click_card(self, pos: Tuple[int, int]):
        if not self.current_player.is_human:
            return

        for player_index, player in enumerate(self.players):
            y_position = 100 + player_index * 150  # Check which player's hand area is clicked
            if y_position <= pos[1] <= y_position + self.CARD_HEIGHT:
                if player == self.current_player:  # Check if the clicked player is the current player
                    card_index = (pos[0] - self.CARD_LEFT_MARGIN) // self.CARD_SPACING

                    if 0 <= card_index < len(player.hand):
                        if self.current_player.exist_valid_group():
                            if card_index in self.selected_cards:  # If the card is already selected, remove it from the selection while clicking; Otherwise, add it to the selection while clicking
                                self.selected_cards.remove(card_index)
                            else:
                                self.selected_cards.append(card_index)
                        else:
                            self.message = "No valid groups to discard"
                break

    def human_draw(self):
        if self.turn_state['action_taken']:
            if self.turn_state['has_taken']:
                self.message = "Cannot draw - already took a card from another player this turn"
            elif self.turn_state['cards_drawn'] >= 3:
                self.message = "Cannot draw - already drew maximum 3 cards this turn"
            else:
                self.message = "Cannot draw - already took an action this turn"
            return

        if len(self.current_player.hand) >= 20:
            self.message = "Cannot draw - hand already has 20 cards"
            return

        card = self.deck.pop()
        self.current_player.add_card(card)
        self.turn_state['cards_drawn'] += 1
        self.turn_state['has_drawn'] = True
        self.message = f"{self.current_player.name} drew {card[0]} {card[1]}"

        if self.turn_state['cards_drawn'] == 3:
            self.turn_state['action_taken'] = True
            self.message += " (reached maximum draw limit 3 for this turn)"
        else:
            self.message += f" ({3 - self.turn_state['cards_drawn']} draws remaining)"

        self.check_and_display_valid_groups()

    def human_select_take(self):
        if self.turn_state['has_drawn']:
            self.message = "Cannot take - already drew cards this turn"
            return

        if self.turn_state['action_taken']:
            if self.turn_state['has_taken']:
                self.message = "Cannot take - already took a card this turn"
            else:
                self.message = "Cannot take - already took an action this turn"
            return

        if len(self.current_player.hand) >= 20:
            self.message = "Cannot take - hand already has 20 cards"
            return

        self.showing_player_select_buttons = True
        self.turn_state['waiting_for_take'] = True
        self.message = "Select a player to take one card from"

    def human_take(self, target_player: Player):
        if not self.turn_state['waiting_for_take']:
            return

        taken_card = random.choice(target_player.hand)
        target_player.remove_card(taken_card)
        self.current_player.add_card(taken_card)

        self.turn_state['action_taken'] = True
        self.turn_state['has_taken'] = True
        self.turn_state['waiting_for_take'] = False
        self.showing_player_select_buttons = False
        self.player_select_buttons.clear()

        self.message = f"{self.current_player.name} took {taken_card[0]} {taken_card[1]} from {target_player.name}"

        if len(target_player.hand) == 0:
            self.game_phase = GamePhase.GAME_OVER
            self.message = f"{target_player.name} wins!"
            self.update_screen()
            self.show_game_over_popup(target_player.name)
        else:
            self.check_and_display_valid_groups()

    def human_discard(self):
        if not self.current_player.exist_valid_group():
            self.message = "No valid groups available to discard"
            return

        if not self.selected_cards:
            self.message = "No cards selected"
            return

        selected_cards = [self.current_player.hand[i] for i in self.selected_cards]
        collection = CollectionOfCards(selected_cards)

        if not collection.is_valid_group():
            self.message = "Not a valid group"
            return

        for card in selected_cards:
            self.current_player.remove_card(card)
            self.deck.append(card)
        random.shuffle(self.deck)

        self.selected_cards = []
        self.message = "Group discarded"

        if len(self.current_player.hand) == 0:
            self.game_phase = GamePhase.GAME_OVER
            self.message = f"{self.current_player.name} wins!"
            self.update_screen()
            self.show_game_over_popup(self.current_player.name)
        else:
            if self.current_player.exist_valid_group():  # Check if there are still valid groups after discarding
                valid_groups = self.current_player.all_valid_groups_with_largest_length()
                group_descriptions = []
                for i, group in enumerate(valid_groups, 1):
                    group_desc = ', '.join(f"{card[0]} {card[1]}" for card in group)
                    group_descriptions.append(f"{i}. {group_desc}")

                self.message = "More valid groups found! Select cards and click Discard to remove them"
            else:
                self.message = "Group discarded"

    def human_pass(self):
        if self.turn_state['has_drawn']:
            self.message = "Cannot pass - already drew cards this turn"
            return
        if self.turn_state['action_taken']:
            if self.turn_state['has_taken']:
                self.message = "Cannot pass - already took a card this turn"
            else:
                self.message = "Cannot pass - already took an action this turn"
            return

        self.turn_state['action_taken'] = True
        self.message = f"{self.current_player.name} passed turn"
        self.human_start_next_turn()

    def human_start_next_turn(self):
        if not (self.turn_state['action_taken'] or self.turn_state['has_drawn']):
            self.message = "You must take an action before starting next turn"
            return

        self.selected_cards = []
        self.turn_state = self.initial_turn_state()
        current_index = self.players.index(self.current_player)
        self.current_player = self.players[(current_index + 1) % len(self.players)]
        self.message = f"{self.current_player.name}'s turn"

    def check_and_display_valid_groups(self) -> bool:
        if self.current_player.exist_valid_group():
            if self.current_player.is_human:
                self.message = "You have valid groups! Select cards and click Discard to remove them"
                return True
            else:
                valid_groups = self.current_player.all_valid_groups_with_largest_length()
                group_descriptions = []
                for i, group in enumerate(valid_groups, 1):
                    group_desc = ', '.join(f"{card[0]} {card[1]}" for card in group)
                    group_descriptions.append(f"{i}. {group_desc}")

                self.message = f"{self.current_player.name}'s valid groups: {' | '.join(group_descriptions)}"
                self.update_screen()
                pygame.time.wait(2000)
                return True
        return False

    def highlight_human_valid_groups(self):
        if not self.selected_cards:
            return

        selected_cards = [self.current_player.hand[i] for i in self.selected_cards]
        collection = CollectionOfCards(selected_cards)

        if collection.is_valid_group():  # Display green outline if valid group
            for card_index in self.selected_cards:
                x = self.CARD_LEFT_MARGIN + card_index * self.CARD_SPACING
                y = 100 + self.players.index(self.current_player) * 150
                pygame.draw.rect(self.screen, self.GREEN, (x, y, self.CARD_WIDTH, self.CARD_HEIGHT), 3)
        else:  # Display red outline if invalid group
            for card_index in self.selected_cards:
                x = self.CARD_LEFT_MARGIN + card_index * self.CARD_SPACING
                y = 100 + self.players.index(self.current_player) * 150
                pygame.draw.rect(self.screen, self.RED, (x, y, self.CARD_WIDTH, self.CARD_HEIGHT), 3)

    def computer_turn(self):
        pygame.time.wait(1000)

        if self.check_and_display_valid_groups():
            self.computer_discard()

        if len(self.current_player.hand) >= 20:  # Check if the current computer player has reached the maximum hand size. If so, pass turn.
            self.message = f"{self.current_player.name} has reached maximum hand size, passing turn"
            self.update_screen()
            pygame.time.wait(2000)
            self.computer_start_next_turn()
            return

        game_state = {
            'current_player': self.current_player,
            'other_players': [p for p in self.players if p != self.current_player],
            'deck_cards': self.deck,
            'deck_size': len(self.deck)
        }

        self.message = f"{self.current_player.name} is thinking..."
        self.update_screen()
        pygame.time.wait(1500)

        action, target_player = self.current_player.choose_action(game_state)

        if action == 'draw':
            self.computer_draw(game_state)
        elif action == 'take':
            self.computer_take(target_player)
        elif action == 'pass':
            self.message = f"{self.current_player.name} chooses to pass"
            self.update_screen()
            pygame.time.wait(1500)
            self.computer_start_next_turn()
            return

        self.computer_start_next_turn()

    def computer_take(self, target_player: Player):
        if target_player.hand:
            taken_card = random.choice(target_player.hand)
            target_player.remove_card(taken_card)
            self.current_player.add_card(taken_card)
            self.message = f"{self.current_player.name} took {taken_card[0]} {taken_card[1]} from {target_player.name}"
            self.update_screen()
            pygame.time.wait(2000)

            if len(target_player.hand) == 0:
                self.game_phase = GamePhase.GAME_OVER
                self.message = f"{target_player.name} wins!"
                self.update_screen()
                self.show_game_over_popup(target_player.name)

            if self.check_and_display_valid_groups():
                self.computer_discard()

            self.update_screen()
            pygame.time.wait(1500)

    def computer_draw(self, game_state: Dict):
        drawn_cards = []

        for i in range(3):
            if len(self.current_player.hand) >= 20:
                self.message = f"{self.current_player.name} has reached maximum hand size, cannot draw anymore"
                self.update_screen()
                pygame.time.wait(2000)
                return

            card = self.deck.pop()
            self.current_player.add_card(card)
            drawn_cards.append(card)

            self.message = f"{self.current_player.name} drew {card[0]} {card[1]} \n Has drew: {', '.join(f'{card[0]} {card[1]}' for card in drawn_cards)}"
            self.update_screen()
            pygame.time.wait(1500)

            if self.check_and_display_valid_groups():
                self.computer_discard()

            self.update_screen()
            pygame.time.wait(1500)

            if i < 2:
                continue_draw = self.current_player.continue_draw(game_state)
                if continue_draw == 0:
                    break

    def computer_discard(self):
        largest_group = self.current_player.largest_valid_group()
        if largest_group:
            for card in largest_group:
                self.current_player.remove_card(card)
                self.deck.append(card)
            random.shuffle(self.deck)
            self.message = f"{self.current_player.name} discarded group: {', '.join(f'{card[0]} {card[1]}' for card in largest_group)}"
            self.update_screen()
            pygame.time.wait(2000)

            if len(self.current_player.hand) == 0:
                self.game_phase = GamePhase.GAME_OVER
                self.message = f"{self.current_player.name} wins!"
                self.update_screen()
                self.show_game_over_popup(self.current_player.name)

    def highlight_computer_valid_groups(self):
        pass

    def update_screen(self):
        """
        Update the screen to display the current game state
        """
        self.screen.fill(self.BACKGROUND_COLOR)
        self.screen.blit(self.background, (0, 0))
        self.game_screen()
        pygame.display.flip()

    def computer_start_next_turn(self):
        self.selected_cards = []
        self.turn_state = self.initial_turn_state()
        current_index = self.players.index(self.current_player)
        self.current_player = self.players[(current_index + 1) % len(self.players)]
        self.message = f"{self.current_player.name}'s turn"

        self.check_and_display_valid_groups()

    def start_game(self, selected_computers: List[ComputerPlayer]):
        self.players = [Player("Human Player", is_human=True)]
        self.players.extend(selected_computers)

        for player in self.players:
            for _ in range(5):
                if self.deck:
                    player.add_card(self.deck.pop())

        self.current_player = self.players[0]
        self.game_phase = GamePhase.PLAYER_TURN
        self.message = "Game started!"
        self.turn_state = self.initial_turn_state()

        self.check_and_display_valid_groups()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_phase == GamePhase.SETUP:
                        self.click_on_setup(event.pos)
                    elif self.game_phase == GamePhase.PLAYER_TURN:
                        self.click_in_game(event.pos)

            self.screen.fill(self.BACKGROUND_COLOR)
            self.screen.blit(self.background, (0, 0))

            if self.game_phase == GamePhase.SETUP:
                self.setup_screen()
            elif self.game_phase == GamePhase.PLAYER_TURN:
                self.game_screen()
                if self.current_player and not self.current_player.is_human:
                    self.computer_turn()

            pygame.display.flip()
            self.clock.tick(self.FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
