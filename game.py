import pygame
import os
from card import Card
from typing import List, Tuple, Dict, Optional, Set
from player import Player
from collection_of_cards import CollectionOfCards
import random
from computer_player import ComputerPlayer, RandomStrategyPlayer, ExpectationValueStrategyPlayer, ProbabilityStrategyPlayer
from animations import CardAnimation  


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

        # Card layout constants
        self.CARD_WIDTH = 60
        self.CARD_HEIGHT = 100
        self.CARD_LEFT_MARGIN = 20
        self.CARD_SPACING = 65

        # Colours
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BACKGROUND_COLOR = (34, 139, 34)

        # button positions
        self.button_positions = {
            'finish draw': pygame.Rect(self.width - 150, self.height - 100, 120, 80),
            'draw': pygame.Rect(self.width - 150, self.height - 180, 120, 80),
            'take': pygame.Rect(self.width - 150, self.height - 260, 120, 80),
            'discard': pygame.Rect(self.width - 150, self.height - 340, 120, 80),
            'pass': pygame.Rect(self.width - 150, self.height - 420, 120, 80),
            'next': pygame.Rect(self.width - 150, self.height - 500, 120, 80)
        }

        self.load_assets()

        self.computer_buttons = {}      #Computer players select buttons
        self.selected_computers = []

        self.game_phase = GamePhase.SETUP 

        self.players: List[Player] = []         #Players
        self.current_player = None             #Current player

        self.deck: List[Card] = [              #Deck
            Card(colour, number, 
                 card_width=self.CARD_WIDTH, 
                 card_height=self.CARD_HEIGHT,
                 position=(0, 0))
            for colour in {'red', 'blue', 'green', 'yellow'} 
            for number in range(1, 11) 
            for _ in range(2)
        ]
        random.shuffle(self.deck)

        self.selected_cards: List[Card] = []   #Selected cards by human player pointer

        self.turn_state = self.initial_turn_state()         

        self.player_select_buttons = {}        #Select buttons for human player to take card from other players
        self.showing_player_select_buttons = False

        self.target_player = None              #Player to take card from
        self.taken_card = None                 #Card taken by human player pointer
        
        self.message = ""                      #Messages
        self.current_turn_text = ""            #Display who's turn

        self.deck_area = pygame.Rect(50, 0, self.CARD_WIDTH, self.CARD_HEIGHT)   #Deck area
        self.temp_draw_area = pygame.Rect(0, 0, self.CARD_WIDTH, self.CARD_HEIGHT) #After drawing cards, temporary area to display drawn cards

        Card.initialize_back_image(self.CARD_WIDTH, self.CARD_HEIGHT)    #Initialize card back image

        self.card_back = pygame.image.load('cards/card_back.jpg')
        self.card_back = pygame.transform.scale(self.card_back, (self.CARD_WIDTH, self.CARD_HEIGHT))

        self.clock = pygame.time.Clock()        #Clock for animation
        self.FPS = 60                           #Frames per second

        #Animation controller instance
        self.card_animation = CardAnimation(
            self.screen,
            self.clock,
            self.card_back,
            self.background,
            self.BACKGROUND_COLOR,
            self.CARD_WIDTH,
            self.CARD_HEIGHT
        )


    def initial_turn_state(self):
        return {
            'has_drawn': False,  #mark if at least one card has been drawn
            'is_drawing': False,  #mark if currently drawing cards
            'is_finished_drawing': False,  #mark if finished drawing cards
            'cards_drawn_count': 0,  #record how many cards have been drawn in this turn
            'drawn_cards': [],  #record all cards drawn in this turn
            'has_taken': False,  #mark if one card has been taken
            'waiting_for_take': False,  #mark if having clicked 'Take' button and waiting for selecting a card to take
            'has_passed': False  #mark if having passed this turn
        }
    

    def load_assets(self):
        background_image = pygame.image.load(os.path.join('backgrounds', 'gradient_background.png'))
        self.background = pygame.transform.scale(background_image, (self.width, self.height))

        self.buttons = {}
        for button_name in ['draw', 'finish draw', 'take', 'discard', 'pass', 'next']:
            button_image = pygame.image.load(os.path.join('buttons', f'{button_name}_normal.png'))
            self.buttons[button_name] = pygame.transform.scale(button_image, (self.button_positions[button_name].width, self.button_positions[button_name].height))
            

    def game_screen(self, draw_temp_cards=True):
        """Screen displayed during the game"""
        font = pygame.font.Font(None, 36)

        if self.current_player:                                                 #Display who's turn at the top of the screen
            turn_text = f"Current Turn: {self.current_player.name}"
            turn_surface = font.render(turn_text, True, self.BLACK) 
            turn_rect = turn_surface.get_rect(centerx=self.width // 2, top=20)
            self.screen.blit(turn_surface, turn_rect)
        
        for i, player in enumerate(self.players):                              #Display cards in players' hands
            self.display_player_hand(player, 100 + i * 150)
      
        last_player_y = 100 + (len(self.players) - 1) * 150   #Calculate the position of the deck area
        deck_y = last_player_y + 120  
        self.deck_area.y = deck_y

        deck_text = font.render(f"Deck: {len(self.deck)} cards", True, self.BLACK)   #Display text: the number of cards in the deck
        deck_text_rect = deck_text.get_rect(left=self.deck_area.right + 20, centery=self.deck_area.centery)
        self.screen.blit(deck_text, deck_text_rect)

        self.temp_draw_area.x = deck_text_rect.right + 20  #Position of the temporary draw area is right to the deck text
        self.temp_draw_area.y = deck_y

        if self.deck:                              # Display the deck with a slight offset to create a stacked effect
            for i in range(min(10, len(self.deck))):
                deck_rect = self.deck_area.copy()
                deck_rect.x += i * 2  
                deck_rect.y += i * 2  
                self.screen.blit(self.card_back, deck_rect)

        if draw_temp_cards and self.turn_state['is_drawing']:    # Display drawn cards in temporary area if currently drawing
            for i, _ in enumerate(self.turn_state['drawn_cards']):
                x = self.temp_draw_area.x + i * 20
                y = self.temp_draw_area.y
                self.screen.blit(self.card_back, (x, y))

        if self.current_player and self.current_player.is_human:  #Display action buttons if it's human player's turn
            self.display_action_buttons()

        if self.selected_cards:                                    #Highlight valid groups if human player has selected cards
            self.highlight_human_valid_groups()

        self.display_valid_groups_panel()                          #Display current valid groups in a panel

        if self.message or self.turn_state['is_drawing']:         #Display messages
            messages = []
            if self.turn_state['is_drawing']:                      #Display messages when drawing cards (messages are different when reaching maximum draw limit)
                if self.turn_state['cards_drawn_count'] == 3:
                    messages.append(f"{self.current_player.name} has drew {self.turn_state['cards_drawn_count']} cards (reached maximum draw limit 3 for this turn)")
                else:
                    messages.append(f"{self.current_player.name} has drew {self.turn_state['cards_drawn_count']} cards ({3 - self.turn_state['cards_drawn_count']} draws remaining)")
                if self.message and self.message != messages[0]:
                    messages.extend(self.message.split('\n'))
            else:
                messages = self.message.split('\n')

            for i, message_line in enumerate(messages):        #Display messages line by line
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

        if self.showing_player_select_buttons:                      #Display select buttons for human player to take card from other players after clicking 'Take' 
            self.display_player_select_buttons()


    def setup_screen(self):  
        """Screen displayed when setting up the game"""                                     
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
            ("Computer 4 (Calculating Expectation Strategy)", ExpectationValueStrategyPlayer("Computer 4")),
            ("Computer 5 (Probability Strategy)", ProbabilityStrategyPlayer("Computer 5")),
            ("Computer 6 (Probability Strategy)", ProbabilityStrategyPlayer("Computer 6"))
        ]

        button_height = 50
        button_spacing = 20
        for i, (name, computer_player) in enumerate(available_computers):   #Display computer player select buttons
            button_rect = pygame.Rect(
                self.width // 2 - 150,
                220 + i * (button_height + button_spacing),
                300,
                button_height
            )

            is_selected = any(comp.name == computer_player.name for comp in self.selected_computers)  #Check if this computer player is selected

            if is_selected:
                pygame.draw.rect(self.screen, (200, 255, 200), button_rect)
            else:
                pygame.draw.rect(self.screen, self.WHITE, button_rect)

            pygame.draw.rect(self.screen, self.BLACK, button_rect, 2)
            text = font.render(name, True, self.BLACK)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)

            self.computer_buttons[name] = (button_rect, computer_player)

        if len(self.selected_computers) > 0:      #Display 'Start Game' button if at least one computer player is selected
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
        for action, rect in self.button_positions.items():    #Display all the action buttons
            if action == 'finish draw':                       #Display 'Finish Draw' button if currently drawing cards, otherwise don't display this button
                if self.turn_state['is_drawing']:
                    self.screen.blit(self.buttons[action], rect)
            else:
                self.screen.blit(self.buttons[action], rect)


    def display_player_hand(self, player: Player, y_position: int):
        font = pygame.font.Font(None, 36)
        text = font.render(f"{player.name}'s hand", True, self.BLACK)
        self.screen.blit(text, (self.CARD_LEFT_MARGIN, y_position - 30))

        x_spacing = 70   
        start_x = max(50, (self.width - (len(player.cards) * x_spacing)) // 2)   #Calculate the starting x position of the first card
        
        for i, card in enumerate(player.cards):                                  #Calculate and set each card position with animation
            new_x = start_x + i * x_spacing
            card.set_position(new_x, y_position, animate=True)
      
        for card in player.cards:                                              
            card.update()  
            self.screen.blit(card.image, card.rect)


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
        """Display all current valid groups in a panel"""
        if not self.current_player.exist_valid_group():
            return

        font = pygame.font.Font(None, 36)
        valid_groups = self.current_player.all_valid_groups()

        panel_x = self.width - 500
        panel_y = self.height - 420

        title = "Current Valid Groups:"
        title_text = font.render(title, True, self.BLACK)
        self.screen.blit(title_text, (panel_x, panel_y))

        y_offset = 40
        for i, group in enumerate(valid_groups):
            group_desc = ', '.join(f"{card.color} {card.number}" for card in group)
            group_text = font.render(f"{i + 1}. {group_desc}", True, self.BLACK)
            self.screen.blit(group_text, (panel_x, panel_y + y_offset + i * 30))


    def show_game_over_popup(self, winner_name: str):
        """If one player wins, display a popup"""
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
        """Human player clicks on the setup screen"""
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
        """Human player clicks action buttons or player select buttons on the game screen"""
        if not self.current_player.is_human:
            return

        if self.showing_player_select_buttons:
            for player_name, button_rect in self.player_select_buttons.items():  #Check which player select button is clicked
                if button_rect.collidepoint(pos):   
                    self.target_player = None
                    for player in self.players:
                        if player.name == player_name:
                            self.target_player = player
                            break
                    self.human_take(self.target_player)
                    return

        for action, rect in self.button_positions.items():  
            if rect.collidepoint(pos):
                if action != 'take':
                    self.showing_player_select_buttons = False
                    self.turn_state['waiting_for_take'] = False

                if action == 'finish draw':
                    if self.turn_state['is_drawing']:
                        self.human_finish_drawing()
                elif action == 'draw':
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

        if self.turn_state['waiting_for_take']:     #Card clicked when human player is taking a card from other players
            for card in self.target_player.cards:
                if card.contains_point(pos):
                    self.taken_card = card
                    self.turn_state['waiting_for_take'] = False
                    self.turn_state['has_taken'] = True
                    card.selected = True
                    return

        for card in self.current_player.cards:    #Card clicked when human player is selecting cards to discard
            if card.contains_point(pos):
                if self.current_player.exist_valid_group():
                    if card in self.selected_cards:
                        self.selected_cards.remove(card)
                        card.selected = False
                        card.invalid = False  
                    else:
                        self.selected_cards.append(card)
                        card.selected = True
                    self.highlight_human_valid_groups()  
                else:
                    self.message = "No valid groups to discard"
                break
            

    def card_hover(self, pos: Tuple[int, int]):
        """Highlight the card that is hovered"""
        if not self.current_player or not self.current_player.is_human:
            return

        for card in self.current_player.cards:     #Reset hover state for all cards
            card.hover = False

        for card in self.current_player.cards:      #Check for which card should be hovered in current player's hand
            if card.contains_point(pos):
                card.hover = True
                break


    def human_draw(self):
        if self.turn_state['is_finished_drawing']:
            self.message = "Cannot draw - already finished drawing this turn"
            return

        if self.turn_state['cards_drawn_count'] >= 3:
            self.message = "Cannot draw - already drew maximum 3 cards this turn"
            return

        if len(self.current_player.cards) >= 20:
            self.message = "Cannot draw - hand already has 20 cards"
            return

        card = self.deck.pop()                                          #Draw a card from the deck each time human player clicks 'Draw'
        
        start_pos = (self.deck_area.x + min(5, len(self.deck)) * 2,     #Calculate the starting position and target position of the drawn card animation
                self.deck_area.y + min(5, len(self.deck)) * 2)
        target_pos = (self.temp_draw_area.x + self.turn_state['cards_drawn_count'] * 20,
                     self.temp_draw_area.y + self.turn_state['cards_drawn_count'] * 2)
        
        self.card_animation.draw_to_temp_draw_area(start_pos, target_pos, self.game_screen)  #Animate the drawn card from deck to the temporary draw area

        self.turn_state['drawn_cards'].append(card)
        self.turn_state['is_drawing'] = True    
        self.turn_state['cards_drawn_count'] += 1
        self.turn_state['has_drawn'] = True
        
        self.message = f"{self.current_player.name} has drew {self.turn_state['cards_drawn_count']} cards"
        if self.turn_state['cards_drawn_count'] == 3:
            self.message += " (reached maximum draw limit 3 for this turn)"
        else:
            self.message += f" ({3 - self.turn_state['cards_drawn_count']} draws remaining)"

    def human_finish_drawing(self):
        if not self.turn_state['is_drawing']:
            self.message = "Cannot finish drawing - not currently drawing"
            return

        temp_area_pos = (self.temp_draw_area.x, self.temp_draw_area.y)           #Drawn cards animation starting from the temporary draw area
        hand_pos = (self.CARD_LEFT_MARGIN, self.current_player.cards[0].rect.y)  #Drawn cards animation targeting at the leftmost end of current player's hand which is the temporary display area
        
        card_positions = [(temp_area_pos[0] + i * 30, temp_area_pos[1])        #Calculate the positions to display the flipping animation of drawn cards
                         for i in range(len(self.turn_state['drawn_cards']))]
        self.card_animation.flip_cards_animation(                                #Animate the flipping of drawn cards
            self.turn_state['drawn_cards'],
            card_positions,
            lambda: self.game_screen(draw_temp_cards=False)
        )
        
        self.card_animation.spread_cards_animation(                                #Animate the spreading of drawn cards after flipping
            self.turn_state['drawn_cards'],
            temp_area_pos, 20, 70,
            lambda: self.game_screen(draw_temp_cards=False)
        )
        
        self.message = f"{self.current_player.name} finished drawing cards"
        self.message += f"\nHas drew: {', '.join(f'{card.color} {card.number}' for card in self.turn_state['drawn_cards'])}"

        self.turn_state['is_drawing'] = False
        
        self.card_animation.display_cards_temporarily(                                #Display temporarily the drawn cards in the temporary draw area
            self.turn_state['drawn_cards'],
            temp_area_pos, 70,
            lambda: self.game_screen(draw_temp_cards=False)
        )
        
        self.card_animation.move_to_temp_display_area(                                #Animate the moving of drawn cards to the temporary display area at the leftmost end of current player's hand
            self.turn_state['drawn_cards'],
            temp_area_pos, hand_pos, 70,
            lambda: self.game_screen(draw_temp_cards=False)
        )
        
        self.card_animation.show_in_temp_display_area(                                #Display the drawn cards in the temporary display area for a short period of time
            self.turn_state['drawn_cards'],
            (self.CARD_LEFT_MARGIN, self.current_player.cards[0].rect.y),
            20,
            lambda: self.game_screen(draw_temp_cards=False)
        )

        for card in self.turn_state['drawn_cards']:                                    #Add the drawn cards to current player's hand
            self.current_player.add_card(card)
        
        animation_frames = 0                                                           #Final animation to complete card positioning
        while animation_frames < 45:
            self.screen.fill(self.BACKGROUND_COLOR)
            self.screen.blit(self.background, (0, 0))
            self.game_screen(draw_temp_cards=False)
            
            for card in self.current_player.cards:
                card.update()
            self.update_screen()
            
            animation_frames += 1
            self.clock.tick(40)

        self.turn_state['is_finished_drawing'] = True
        self.turn_state['drawn_cards'] = []
        
        self.check_and_display_valid_groups()                                        #Check and display valid groups after drawing

    def human_select_take(self):
        if self.turn_state['is_drawing']:
            self.message = "Cannot take - please finish drawing cards first"
            return

        if self.turn_state['has_taken']:
            self.message = "Cannot take - already took a card this turn"
            return

        if len(self.current_player.cards) >= 20:
            self.message = "Cannot take - hand already has 20 cards"
            return

        self.showing_player_select_buttons = True
        self.turn_state['waiting_for_take'] = True
        self.message = "Select a player to take one card from"


    def human_take(self, target_player: Player):
        if not self.turn_state['waiting_for_take']:
            return

        self.card_animation.flip_player_cards_to_back(                            #Animate the flipping of target player's cards from face up to face down
            target_player,
            lambda: self.game_screen()
        )
        
        pygame.time.wait(200)

        center_x = target_player.cards[0].rect.x + len(target_player.cards) * 35 // 2  #Calculate the center position of displaying the shuffling animation
        center_y = target_player.cards[0].rect.y
        self.card_animation.shuffle_in_player_hand(                                #Animate the shuffling of target player's cards
            target_player,
            (center_x, center_y),
            lambda: self.game_screen()
        )

        random.shuffle(target_player.cards)                                        #Acturally shuffle the cards in target player's hand
        
        spacing = 70                                                                
        start_x = max(50, (self.width - (len(target_player.cards) * spacing)) // 2)
        y_position = target_player.cards[0].rect.y
        
        for i, card in enumerate(target_player.cards):                              #Again set the position of the cards after simulating shuffling
            card.face_down = True
            card.set_position(start_x + i * spacing, y_position)
        
        self.target_player = target_player                                         # Set up for card selection
        self.turn_state['waiting_for_take'] = True
        self.taken_card = None
        self.message = "Click a card to take"
        
        while self.turn_state['waiting_for_take']:                                  #Wait for human player to select and click a card to take
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.click_card(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.card_hover(event.pos)
        
            self.update_screen()
            self.clock.tick(self.FPS)
        
        if self.taken_card:
            self.taken_card.face_down = False                                          #Set the taken card to face up after human player clicks on it
            original_pos = (self.taken_card.rect.x, self.taken_card.rect.y)            #The original position and the target position (temporary display area) of the taken card animation
            temp_display_pos = (self.CARD_LEFT_MARGIN, self.current_player.cards[0].rect.y) 
            
            target_player.cards.remove(self.taken_card)                              #Remove the taken card from target player's hand
            self.taken_card.reset_state()                                             #Reset the state of the taken card to default

            self.card_animation.move_to_temp_display_area(                            #Animate the moving of the taken card to the temporary display area
                [self.taken_card],
                original_pos, temp_display_pos, 0,
                lambda: self.game_screen()
            )
            
            self.card_animation.show_in_temp_display_area(                            #Display the taken card in the temporary display area for a short period of time
                [self.taken_card],
                temp_display_pos,
                0,
                lambda: self.game_screen()
            )
            
            self.current_player.add_card(self.taken_card)                            #Add the taken card to current player's hand
            self.turn_state['has_taken'] = True
            self.showing_player_select_buttons = False
            self.player_select_buttons.clear()

            self.message = f"{self.current_player.name} took {self.taken_card.color} {self.taken_card.number} from {target_player.name}"

            if len(target_player.cards) == 0:                                       #If target player has no cards left, game over
                self.game_phase = GamePhase.GAME_OVER
                self.message = f"{target_player.name} wins!"
                self.update_screen()
                self.show_game_over_popup(target_player.name)
            
            for card in target_player.cards:                                        #Flip back the remaining cards in target player's hand
                card.face_down = False
                card.update()
            
            self.taken_card = None
            self.target_player = None
            
            self.check_and_display_valid_groups()                                    #Check and display valid groups after taking


    def human_discard(self):
        if self.turn_state['is_drawing']:
            self.message = "Cannot discard - please finish drawing cards first"
            return

        if not self.current_player.exist_valid_group():
            self.message = "No valid groups available to discard"
            return

        if not self.selected_cards:
            self.message = "No cards selected"
            return

        collection = CollectionOfCards(self.selected_cards)
        if not collection.is_valid_group():
            self.message = "Not a valid group"
            return

        CARDS_DELAY = 5                                                          #Delay between cards being discarded
        
        for card_index, card in enumerate(self.selected_cards):
            self.current_player.remove_card(card)
            start_pos = (card.rect.x, card.rect.y)                                #Starting position of the discard animation is the position of this card
            target_pos = (self.deck_area.x + min(5, len(self.deck)) * 2,          #Target position of the discard animation is the position of the top card of the deck
                         self.deck_area.y + min(5, len(self.deck)) * 2)

            for _ in range(card_index * CARDS_DELAY):                     
                self.update_screen()
                self.clock.tick(self.FPS)

            self.card_animation.discard_card_animation(                            #Animate the discarding of the selected cards
                card, start_pos, target_pos, self.game_screen
            )
            
            card.reset_state()
            self.deck.append(card)

        random.shuffle(self.deck)
        self.card_animation.shuffle_animation(                                    #Animate the shuffling of the deck
            self.deck_area,
            redraw_game_screen=self.game_screen
        )

        self.selected_cards = []
        self.current_player.clear_selections()
        self.message = "Group discarded"

        if len(self.current_player.cards) == 0:
            self.game_phase = GamePhase.GAME_OVER
            self.message = f"{self.current_player.name} wins!"
            self.update_screen()
            self.show_game_over_popup(self.current_player.name)
        else:
            if self.current_player.exist_valid_group():                            # Check if there are still valid groups after discarding
                valid_groups = self.current_player.all_valid_groups()
                group_descriptions = []
                for i, group in enumerate(valid_groups, 1):
                    group_desc = ', '.join(f"{card.color} {card.number}" for card in group)
                    group_descriptions.append(f"{i}. {group_desc}")
                self.message = "More valid groups found! Select cards and click Discard to remove them"
            else:
                self.message = "Group discarded"


    def human_pass(self):
        if self.turn_state['has_drawn'] or self.turn_state['has_taken']:
            self.message = "Cannot pass - already took other actions this turn"
            return
        
        self.message = f"{self.current_player.name} passed turn"
        self.turn_state['has_passed'] = True
        self.human_start_next_turn()


    def human_start_next_turn(self):
        """Start the next turn after human player passes or clicked 'Next'"""
        if self.turn_state['is_drawing']:
            self.message = "Have you finished drawing cards? Please click 'Finish Draw' button before starting next turn"
            return

        if not self.turn_state['has_drawn'] and not self.turn_state['has_taken'] and not self.turn_state['has_passed']:
            self.message = "You must take an action before starting next turn"
            return

        self.selected_cards = []
        self.turn_state = self.initial_turn_state()
        current_index = self.players.index(self.current_player)                      #Get the index of the current player
        self.current_player = self.players[(current_index + 1) % len(self.players)]  #Set the player with the next index as the current player
        self.message = f"{self.current_player.name}'s turn"


    def check_and_display_valid_groups(self) -> bool:
        if self.current_player.exist_valid_group():
            if self.current_player.is_human:
                self.message = "You have valid groups! Select cards and click Discard to remove them"
                return True
            else:
                valid_groups = self.current_player.all_valid_groups()
                group_descriptions = []
                for i, group in enumerate(valid_groups, 1):
                    group_desc = ', '.join(f"{card.color} {card.number}" for card in group)
                    group_descriptions.append(f"{i}. {group_desc}")

                self.message = f"{self.current_player.name}'s valid groups: {' | '.join(group_descriptions)}"
                self.update_screen()
                pygame.time.wait(2000)
                return True
        return False
    

    def highlight_human_valid_groups(self):
        if not self.selected_cards:
            for card in self.current_player.cards:
                card.invalid = False
                card.update()
            return

        collection = CollectionOfCards(self.selected_cards)  
        is_valid = collection.is_valid_group()

        for card in self.current_player.cards:   
            if card in self.selected_cards:
                card.invalid = not is_valid
            else:
                card.invalid = False
            card.update()


    def computer_turn(self):
        pygame.time.wait(1000)

        if self.check_and_display_valid_groups():
            self.computer_discard()

        if len(self.current_player.cards) >= 20:     # Check if the current computer player has reached the maximum hand size. If so, pass turn.
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

        action, draw_count, target_player = self.current_player.choose_first_action(game_state)

        if action == 'draw':
            self.computer_draw(draw_count)
            
        elif action == 'take':
            self.computer_take(target_player)

        elif action == 'pass':
            self.message = f"{self.current_player.name} chooses to pass"
            self.update_screen()
            pygame.time.wait(1500)
            self.computer_start_next_turn()
            return
        
        action, draw_count, target_player = self.current_player.choose_second_action(game_state, action)

        if action == 'draw':
            self.computer_draw(draw_count)
            self.computer_start_next_turn()
        elif action == 'take':
            self.computer_take(target_player)
            self.computer_start_next_turn()
        elif action == 'pass':
            self.computer_start_next_turn()


    def computer_take(self, target_player: Player):
        self.message = f"{self.current_player.name} decided to take a card from {target_player.name}"
        self.update_screen()
        pygame.time.wait(1500)

        self.card_animation.flip_player_cards_to_back(
            target_player,
            lambda: self.game_screen()
        )
        
        pygame.time.wait(200)

        center_x = target_player.cards[0].rect.x + len(target_player.cards) * 35 // 2
        center_y = target_player.cards[0].rect.y
        self.card_animation.shuffle_in_player_hand(
            target_player,
            (center_x, center_y),
            lambda: self.game_screen()
        )

        random.shuffle(target_player.cards)
        
        spacing = 70
        start_x = max(50, (self.width - (len(target_player.cards) * spacing)) // 2)
        y_position = target_player.cards[0].rect.y
        
        for i, card in enumerate(target_player.cards):
            card.face_down = True
            card.set_position(start_x + i * spacing, y_position)

        self.update_screen()
        pygame.time.wait(500)
        
        taken_card = random.choice(target_player.cards)
        self.card_animation.reveal_selected_card(
            taken_card,
            lambda: self.update_screen()
        )

        original_pos = (taken_card.rect.x, taken_card.rect.y)
        temp_display_pos = (self.CARD_LEFT_MARGIN, self.current_player.cards[0].rect.y)
        
        target_player.cards.remove(taken_card)
        taken_card.reset_state()

        self.card_animation.move_to_temp_display_area(
            [taken_card],
            original_pos, temp_display_pos, 0,
            lambda: self.game_screen()
        )
        
        self.card_animation.show_in_temp_display_area(
            [taken_card],
            temp_display_pos,
            0,
            lambda: self.game_screen()
        )

        self.current_player.add_card(taken_card)
        self.message = f"{self.current_player.name} took {taken_card.color} {taken_card.number} from {target_player.name}"

        if len(target_player.cards) == 0:
            self.game_phase = GamePhase.GAME_OVER
            self.message = f"{target_player.name} wins!"
            self.update_screen()
            self.show_game_over_popup(target_player.name)

        for card in target_player.cards:
            card.face_down = False
            card.update()

        animation_frames = 0
        while animation_frames < 50:
            for card in self.current_player.cards:
                card.update()
            self.update_screen()
            animation_frames += 1
            self.clock.tick(40)
        
        pygame.time.wait(500)

        while self.check_and_display_valid_groups():
            self.computer_discard()
            self.update_screen()
            pygame.time.wait(1000)

        self.update_screen()


    def computer_draw(self, draw_count: int):
        self.message = f"{self.current_player.name} decided to draw from deck"
        self.update_screen()
        pygame.time.wait(1500)

        for _ in range(draw_count):
            if len(self.current_player.cards) >= 20:
                self.message = f"{self.current_player.name} has reached maximum hand size"
                self.update_screen()
                return

            card = self.deck.pop()
            
            start_pos = (self.deck_area.x + min(5, len(self.deck)) * 2,
                        self.deck_area.y + min(5, len(self.deck)) * 2)
            target_pos = (self.temp_draw_area.x + self.turn_state['cards_drawn_count'] * 20,
                         self.temp_draw_area.y + self.turn_state['cards_drawn_count'] * 2)
            
            self.card_animation.draw_to_temp_draw_area(start_pos, target_pos, self.game_screen)

            self.turn_state['drawn_cards'].append(card)
            self.turn_state['cards_drawn_count'] += 1
            self.turn_state['is_drawing'] = True
            
            self.message = f"{self.current_player.name} has drew {self.turn_state['cards_drawn_count']} cards"

            if self.turn_state['cards_drawn_count'] == 3:
                self.message += " (reached maximum draw limit 3 for this turn)"
            else:
                self.message += f" ({3 - self.turn_state['cards_drawn_count']} draws remaining)"
            pygame.time.wait(500)

        temp_area_pos = (self.temp_draw_area.x, self.temp_draw_area.y)
        card_positions = [(temp_area_pos[0] + i * 30, temp_area_pos[1]) 
                         for i in range(len(self.turn_state['drawn_cards']))]
        self.card_animation.flip_cards_animation(
            self.turn_state['drawn_cards'],
            card_positions,
            lambda: self.game_screen(draw_temp_cards=False)
        )

        self.card_animation.spread_cards_animation(
            self.turn_state['drawn_cards'],
            temp_area_pos, 20, 70,
            lambda: self.game_screen(draw_temp_cards=False)
        )

        self.message = f"{self.current_player.name} finished drawing cards"
        self.message += f"\nHas drew: {', '.join(f'{card.color} {card.number}' for card in self.turn_state['drawn_cards'])}"

        self.turn_state['is_drawing'] = False
        
        self.card_animation.display_cards_temporarily(
            self.turn_state['drawn_cards'],
            temp_area_pos, 70,
            lambda: self.game_screen(draw_temp_cards=False)
        )

        hand_pos = (self.CARD_LEFT_MARGIN, self.current_player.cards[0].rect.y)
        self.card_animation.move_to_temp_display_area(
            self.turn_state['drawn_cards'],
            temp_area_pos, hand_pos, 70,
            lambda: self.game_screen(draw_temp_cards=False)
        )
        
        self.card_animation.show_in_temp_display_area(
            self.turn_state['drawn_cards'],
            (self.CARD_LEFT_MARGIN, self.current_player.cards[0].rect.y),
            20,
            lambda: self.game_screen(draw_temp_cards=False)
        )
        
        for card in self.turn_state['drawn_cards']:
            self.current_player.add_card(card)
        
        animation_frames = 0
        max_frames = 45
        while animation_frames < max_frames:
            self.screen.fill(self.BACKGROUND_COLOR)
            self.screen.blit(self.background, (0, 0))
            self.game_screen(draw_temp_cards=False)
            
            for card in self.current_player.cards:
                card.update()
            self.update_screen()
            
            animation_frames += 1
            self.clock.tick(40)

        self.turn_state['drawn_cards'] = []

        while self.check_and_display_valid_groups():
            self.computer_discard()
            self.update_screen()
            pygame.time.wait(1000)

        self.update_screen()


    def computer_discard(self):
        largest_group = self.current_player.largest_valid_group()
        if largest_group:
            self.highlight_computer_valid_groups(largest_group)
            self.update_screen()
            pygame.time.wait(1000)

            CARDS_DELAY = 5
            
            for card_index, card in enumerate(largest_group):
                self.current_player.remove_card(card)
                start_pos = (card.rect.x, card.rect.y)
                target_pos = (self.deck_area.x + min(5, len(self.deck)) * 2, 
                             self.deck_area.y + min(5, len(self.deck)) * 2)

                for _ in range(card_index * CARDS_DELAY):
                    self.update_screen()
                    self.clock.tick(self.FPS)

                self.card_animation.discard_card_animation(
                    card, start_pos, target_pos, self.game_screen
                )
                
                card.reset_state()
                self.deck.append(card)

            random.shuffle(self.deck)
            self.card_animation.shuffle_animation(
                self.deck_area,
                redraw_game_screen=self.game_screen
            )
            
            self.message = f"{self.current_player.name} discarded group: {', '.join(f'{card.color} {card.number}' for card in largest_group)}"
            
            animation_frames = 0                                 #Wait for the remaining cards to animate to their new positions
            while animation_frames < 30:
                for card in self.current_player.cards:
                    card.update()
                
                self.update_screen()
                animation_frames += 1
                self.clock.tick(self.FPS)
            
            pygame.time.wait(500)

            if len(self.current_player.cards) == 0:
                self.game_phase = GamePhase.GAME_OVER
                self.message = f"{self.current_player.name} wins!"
                self.update_screen()
                self.show_game_over_popup(self.current_player.name)
            else:
                while self.check_and_display_valid_groups():
                    self.computer_discard()
                    self.update_screen()
                    pygame.time.wait(1000)


    def highlight_computer_valid_groups(self, cards_to_highlight: List[Card]):
        if not cards_to_highlight:
            return

        for card in self.current_player.cards:       #Reset all cards' highlight state
            card.selected = False
            card.update()

        for card in cards_to_highlight:              #Highlight the cards that form valid groups
            card.selected = True
            card.update()

        pygame.display.flip()
        pygame.time.wait(1000)

        

    def update_screen(self):
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
                elif event.type == pygame.MOUSEMOTION:  
                    if self.game_phase == GamePhase.PLAYER_TURN:
                        self.card_hover(event.pos)

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
