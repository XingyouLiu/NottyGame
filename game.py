import sys
import os
'''
sys.stderr.flush()
stderr_fd = sys.stderr.fileno()
devnull = os.open(os.devnull, os.O_WRONLY)
os.dup2(devnull, stderr_fd)
'''

import pygame
import json
from card import Card
from typing import List, Tuple, Dict, Optional, Set
from player import Player
from collection_of_cards import CollectionOfCards
import random
from computer_player import ComputerPlayer, RandomStrategyPlayer, ExpectationValueStrategyPlayer, ProbabilityStrategyPlayer, RulebasedStrategyPlayer
from animations import CardAnimation  

with open("config.json") as config_file:
    config = json.load(config_file)
class GamePhase:
    SETUP = "setup"
    WELCOME = "welcome"
    PLAYER_TURN = "player_turn"
    GAME_OVER = "game_over"


class OptionBox():

    def __init__(self, x, y, w, h, color, highlight_color, font, option_list, selected=0):
        self.color = color
        self.highlight_color = highlight_color
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.option_list = option_list
        self.selected = selected
        self.draw_menu = False
        self.menu_active = False
        self.active_option = -1

    def draw(self, surf):
        pygame.draw.rect(surf, self.highlight_color if self.menu_active else self.color, self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        msg = self.font.render(self.option_list[self.selected], 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center=self.rect.center))

        if self.draw_menu:
            for i, text in enumerate(self.option_list):
                rect = self.rect.copy()
                rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(surf, self.highlight_color if i == self.active_option else self.color, rect)
                msg = self.font.render(text, 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center=rect.center))
            outer_rect = (
            self.rect.x, self.rect.y + self.rect.height, self.rect.width, self.rect.height * len(self.option_list))
            pygame.draw.rect(surf, (0, 0, 0), outer_rect, 2)

    def update(self, event_list):
        mpos = pygame.mouse.get_pos()
        self.menu_active = self.rect.collidepoint(mpos)

        self.active_option = -1
        for i in range(len(self.option_list)):
            rect = self.rect.copy()
            rect.y += (i + 1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break

        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False

        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_active:
                    self.draw_menu = not self.draw_menu
                elif self.draw_menu and self.active_option >= 0:
                    self.selected = self.active_option
                    self.draw_menu = False
                    return self.active_option
        return -1


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        # set bgm volume
        self.bgm_volume = 0.2
        self.bgm_switch = True
        # load bgm
        pygame.mixer.music.load('./sound/rednose.ogg')
        pygame.mixer.music.set_volume(self.bgm_volume)

        # replay bgm
        pygame.mixer.music.play(-1)

        display_info = pygame.display.Info()
        self.width = int(display_info.current_w * 0.98)
        self.height = int(display_info.current_h * 0.95)
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE | pygame.SHOWN)
        pygame.display.set_caption("Notty Game")

        # Card layout constants
        self.CARD_WIDTH = 60
        self.CARD_HEIGHT = 90
        self.CARD_LEFT_MARGIN = 20
        self.CARD_SPACING = 65

        # Colours
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BACKGROUND_COLOR = (34, 139, 34)

        # Font, size and title initialization
        self.title_font = pygame.font.SysFont("impact", 72)
        self.body_font = pygame.font.SysFont("impact", 45)

        self.button_height = 50
        self.button_spacing = 20

        self.title = self.title_font.render("Welcome to Notty Game!", True, self.BLACK)
        self.title_rect = self.title.get_rect(center=(self.width // 2, 100))

        button_width = 120
        button_height = 50  
        button_spacing = 20
        center_buttons = ['finish draw', 'draw', 'take', 'discard', 'pass']
        total_center_buttons = len(center_buttons)
        total_center_width = (button_width * total_center_buttons) + (button_spacing * (total_center_buttons - 1))
        
        center_start_x = (self.width - total_center_width) // 2
        bottom_y = self.height - button_height - 20  
        self.button_positions = {
            'computer_takeover': pygame.Rect(20, bottom_y, button_width, button_height),
            
            'finish draw': pygame.Rect(center_start_x, bottom_y, button_width, button_height),
            'draw': pygame.Rect(center_start_x + (button_width + button_spacing), bottom_y, button_width, button_height),
            'take': pygame.Rect(center_start_x + (button_width + button_spacing) * 2, bottom_y, button_width, button_height),
            'discard': pygame.Rect(center_start_x + (button_width + button_spacing) * 3, bottom_y, button_width, button_height),
            'pass': pygame.Rect(center_start_x + (button_width + button_spacing) * 4, bottom_y, button_width, button_height),
            
            'next': pygame.Rect(self.width - button_width - 20, bottom_y, button_width, button_height)
        }

        strategy_button_spacing = button_height + 5  
        self.computer_strategy_buttons = {
            'X-AGGRESSIVE': pygame.Rect(
                20, 
                bottom_y - (button_height + strategy_button_spacing) * 4,  
                button_width,  
                button_height  
            ),
            'AGGRESSIVE': pygame.Rect(
                20,
                bottom_y - (button_height + strategy_button_spacing) * 3,
                button_width,
                button_height
            ),
            'DEFENSIVE': pygame.Rect(
                20,
                bottom_y - (button_height + strategy_button_spacing) * 2,
                button_width,
                button_height
            ),
            'X-DEFENSIVE': pygame.Rect(
                20,
                bottom_y - (button_height + strategy_button_spacing),
                button_width,
                button_height
            )
        }

        system_button_size = 40  
        system_button_margin = 20  
        system_button_top = 20  
        
        self.system_button_positions = {
            'quit': pygame.Rect(
                self.width - system_button_size - system_button_margin, 
                system_button_top, 
                system_button_size, 
                system_button_size
            ),
            'restart': pygame.Rect(
                self.width - (system_button_size + system_button_margin) * 2, 
                system_button_top, 
                system_button_size, 
                system_button_size
            ),
            'music': pygame.Rect(
                self.width - (system_button_size + system_button_margin) * 3, 
                system_button_top, 
                system_button_size, 
                system_button_size
            )
        }

        #Buttons for AI strategy selection (initially hidden)
        self.showing_computer_strategy_buttons = False

        self.load_assets()

        self.computer_buttons = {}      #Computer players select buttons
        self.selected_computers = []

        self.game_phase = GamePhase.WELCOME

        self.players: List[Player] = []         #Players
        self.current_player = None             #Current player

        self.MAX_HAND_SIZE = 20
        self.INITIAL_HAND_SIZE = 5

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
        self.taken_turn_by_computer = False    #Mark if human let a computer player help take this turn
        self.temp_computer = None              #Temporary computer player
        self.temp_computer_finished = False     #Mark if temporary computer player has finished its operations
        
        self.message = ""                      #Messages
        self.current_turn_text = ""            #Display who's turn

        self.deck_area = pygame.Rect(50, 0, self.CARD_WIDTH, self.CARD_HEIGHT)   #Deck area
        self.temp_draw_area = pygame.Rect(0, 0, self.CARD_WIDTH, self.CARD_HEIGHT) #After drawing cards, temporary area to display drawn cards

        Card.initialize_back_image(self.CARD_WIDTH, self.CARD_HEIGHT)    #Initialize card back image

        self.card_back = pygame.image.load('cards/card_back.png')
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
            self.CARD_HEIGHT,
            self  # 添加game参数
        )

        # Initialization sound
        self.card_draw_sound = pygame.mixer.Sound("./sound/draw_card.ogg")
        self.card_shuffle_sound = pygame.mixer.Sound("./sound/deck_card_shuffle.ogg")
        self.hand_card_shuffle_sound = pygame.mixer.Sound("./sound/card_shuffle.ogg")
        self.game_win_sound = pygame.mixer.Sound("./sound/win.ogg")
        self.game_lose_sound = pygame.mixer.Sound("./sound/lose.ogg")

        # Welcome and setup screen initialization
        self.events = []
        self.strategy_list = config["strategy_list"]
        self.player1 = None
        self.player2 = None
        self.no_of_player = 2

        self.drop_down_button_solo = OptionBox(
            self.width // 2 - 150, 220 + 4 * (self.button_height + self.button_spacing),
            300,
            self.button_height, (150, 150, 150), (150, 255, 150), self.body_font,
            self.strategy_list)

        self.drop_down_button_1 = OptionBox(
            self.width // 2 - 350, 220 + 4 * (self.button_height + self.button_spacing),
                300,
                self.button_height, (150, 150, 150), (150, 255, 150), self.body_font,
            self.strategy_list)

        self.drop_down_button_2 = OptionBox(
            self.width // 2 + 50, 220 + 4 * (self.button_height + self.button_spacing),
            300,
            self.button_height, (150, 150, 150), (150, 255, 150), self.body_font,
            self.strategy_list)


        self._hint_probabilities = {}
        self._hint_expectations = {}


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
        background_image = pygame.image.load(os.path.join('backgrounds', 'background.png'))
        self.background = pygame.transform.scale(background_image, (self.width, self.height))

        # Load normal buttons
        self.buttons = {}
        for button_name in ['draw', 'finish draw', 'take', 'discard', 'pass', 'next', 'computer_takeover']:
            button_image = pygame.image.load(os.path.join('buttons', f'{button_name}_normal.png'))
            self.buttons[button_name] = pygame.transform.scale(button_image, (self.button_positions[button_name].width, self.button_positions[button_name].height))

            banned_button = pygame.image.load(os.path.join('buttons_banned', f'{button_name}_banned.png'))
            self.buttons[f'{button_name}_banned'] = pygame.transform.scale(banned_button, (self.button_positions[button_name].width, self.button_positions[button_name].height))
           
        for strategy in ['DEFENSIVE', 'X-DEFENSIVE', 'AGGRESSIVE', 'X-AGGRESSIVE']:
            button_image = pygame.image.load(os.path.join('buttons', f'{strategy}_normal.png'))
            self.buttons[strategy] = pygame.transform.scale(button_image, (120, 80))

        self.system_buttons = {}
        for button_name in ['quit', 'restart', 'music']:
            button_image = pygame.image.load(os.path.join('buttons', f'{button_name}.png'))
            self.system_buttons[button_name] = pygame.transform.scale(button_image, (
            self.system_button_positions[button_name].width, self.system_button_positions[button_name].height))

        self.player_profile = {}
        for player_name in ['mario','peach','bowser']:
            profile_image = pygame.image.load(os.path.join('players', f'{player_name}.png'))
            self.player_profile[player_name] = pygame.transform.scale(profile_image, (120, 175))

        # 加载take from玩家按钮图片
        self.take_from_buttons = {
            'Bowser': pygame.image.load('buttons/take from bowser.png'),
            'Princess Peach': pygame.image.load('buttons/take from princess peach.png')
        }

    def background_music_control(self):

        if not self.bgm_switch:
            pygame.mixer.music.pause()
        elif self.bgm_switch:
            pygame.mixer.music.unpause()

    def game_screen(self, draw_temp_cards=True):
        """Screen displayed during the game"""
        self.screen.fill(self.BACKGROUND_COLOR)
        self.screen.blit(self.background, (0, 0))

        message_font = pygame.font.Font(None, 28)  
        turn_font = pygame.font.Font(None, 36)

        if self.current_player:
            top_margin = int(self.height * 0.03)  # Use 3% of window height as top margin
            turn_text = f"Current Turn: {self.current_player.name}"
            turn_surface = turn_font.render(turn_text, True, self.BLACK) 
            turn_rect = turn_surface.get_rect(centerx=self.width // 2, top=top_margin)
            self.screen.blit(turn_surface, turn_rect)

            # Display messages below the turn text
            if self.message:
                messages = self.message.split('\n')
                message_y = turn_rect.bottom + 10

                for i, message_line in enumerate(messages):
                    words = message_line.split()
                    lines = []
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + 1 <= 100:
                            current_line.append(word)
                            current_length += len(word) + 1
                        else:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = len(word)
                    if current_line:
                        lines.append(' '.join(current_line))

                    # Display each line centered horizontally
                    for j, line in enumerate(lines):
                        message_text = message_font.render(line, True, self.BLACK)
                        message_rect = message_text.get_rect(
                            centerx=self.width // 2,
                            top=message_y + (i * len(lines) + j) * 25
                        )
                        self.screen.blit(message_text, message_rect)

        #Calculate the total height of the message area (considering up to 2 lines of message)
        message_area_height = top_margin + turn_rect.height + 10 + (2 * 25)  
        
        # Calculate the position of the human player's hand area (above the button area)
        human_cards_y = self.height - 200  # 200 pixels above the button area

        # Calculate the starting position of the computer player's hand area (below the message area)   
        computer_cards_start_y = message_area_height + 25

        # Display all players' hands
        for i, player in enumerate(self.players):
            if player.is_human:
                # The human player's hand is displayed at the bottom
                self.display_player_hand(player, human_cards_y)
            else:
                # Computer player's hand displayed above, with 150 pixels spacing between each player
                computer_index = sum(1 for p in self.players[:i] if not p.is_human)
                self.display_player_hand(player, computer_cards_start_y + computer_index * 150)
      
        # Calculate the position of the last computer player's hand
        last_computer_y = computer_cards_start_y + (len([p for p in self.players if not p.is_human]) - 1) * 150

        # Calculate the vertical position of the deck area (at the midpoint between the last computer player and the human player)
        deck_y = (last_computer_y + human_cards_y) // 2
        # Calculate the horizontal position of the deck area (in the center of the screen)
        deck_x = (self.width - self.CARD_WIDTH) // 2
        self.deck_area.x = deck_x
        self.deck_area.y = deck_y

        # Display the text showing the number of cards remaining in the deck
        deck_text = message_font.render(f"Deck: {len(self.deck)} cards", True, self.BLACK)
        deck_text_rect = deck_text.get_rect(centerx=self.deck_area.centerx, top=self.deck_area.bottom + 50)
        self.screen.blit(deck_text, deck_text_rect)

        # Update the position of the temporary draw area (to the left of the deck area)
        self.temp_draw_area.x = self.deck_area.x - self.CARD_WIDTH - 160  # 160 pixels to the left
        self.temp_draw_area.y = deck_y

        if self.deck:  # Display cards in the deck, creating a stacking effect
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

        self.display_valid_groups_panel()  # Draw Valid groups panel first
        self.display_hint_panel()

        if self.current_player and self.current_player.is_human and not self.taken_turn_by_computer:
            self.display_action_buttons()
            
            if self.showing_computer_strategy_buttons:
                for strategy in ['X-AGGRESSIVE', 'AGGRESSIVE', 'DEFENSIVE', 'X-DEFENSIVE']:
                    rect = self.computer_strategy_buttons[strategy]
                    pygame.draw.rect(self.screen, self.WHITE, rect)
                    pygame.draw.rect(self.screen, self.BLACK, rect, 2)
                    self.screen.blit(self.buttons[strategy], rect)
        elif self.current_player and self.current_player.is_human and self.taken_turn_by_computer and self.temp_computer_finished:
            self.screen.blit(self.buttons['next'], self.button_positions['next'])
        
        if len(self.current_player.cards) >= 20:
            self.screen.blit(self.buttons['next'], self.button_positions['next'])
        
        self.display_system_buttons()
        if self.selected_cards:                                    #Highlight valid groups if human player has selected cards
            self.highlight_human_valid_groups()

        if self.showing_player_select_buttons:                      #Display select buttons for human player to take card from other players after clicking 'Take' 
            self.display_player_select_buttons()

    def welcome_screen(self):
        """Screen displayed when setting up the game"""

        self.title_rect = self.title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(self.title, self.title_rect)

        subtitle = self.body_font.render("Please select how many opponents:", True, self.BLACK)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 240))
        self.screen.blit(subtitle, subtitle_rect)
        
        self.display_system_buttons()
        # Two play modes
        two_player_button = pygame.Rect(
            self.width // 2 - 150,
            220 + (self.button_height + self.button_spacing),
            300,
            self.button_height
        )

        three_player_button = pygame.Rect(
            self.width // 2 - 150,
            220 + (self.button_height + self.button_spacing) * 2,
            300,
            self.button_height
        )
        pygame.draw.rect(self.screen, (150, 255, 150), two_player_button)
        pygame.draw.rect(self.screen, self.BLACK, two_player_button, 2)
        start_text = self.body_font.render("1  Opponent", True, self.BLACK)
        start_rect = start_text.get_rect(center=two_player_button.center)
        self.screen.blit(start_text, start_rect)
        self.computer_buttons['2 Players'] = (two_player_button, None)

        pygame.draw.rect(self.screen, (150, 255, 150), three_player_button)
        pygame.draw.rect(self.screen, self.BLACK, three_player_button, 2)
        start_text = self.body_font.render("2  Opponents", True, self.BLACK)
        start_rect = start_text.get_rect(center=three_player_button.center)
        self.screen.blit(start_text, start_rect)
        self.computer_buttons['3 Players'] = (three_player_button, None)

    def setup_screen_solo(self):
        """Screen displayed when setting up the game"""
        center_x = self.width // 2
        center_y = self.height // 2
        vertical_spacing = 70 

        title_y = center_y - 300  
        self.title_rect = self.title.get_rect(center=(center_x, title_y))
        self.screen.blit(self.title, self.title_rect)

        subtitle = self.body_font.render("Please select who do you want to play with:", True, self.BLACK)
        subtitle_rect = subtitle.get_rect(center=(center_x, title_y + vertical_spacing))
        self.screen.blit(subtitle, subtitle_rect)

        # Profile picture - Under subtitle
        profile_y = title_y + vertical_spacing * 3  
        bowser_rect = self.player_profile['bowser'].get_rect(center=(center_x, profile_y))
        self.screen.blit(self.player_profile['bowser'], bowser_rect)

        # Strategy selection dropdown - Under profile picture
        dropdown_y = profile_y + vertical_spacing * 1  
        dropdown_width = 300
        dropdown_height = self.button_height
        
        # Update the dropdown position
        self.drop_down_button_solo.rect.x = center_x - 150  # Center placement
        self.drop_down_button_solo.rect.y = dropdown_y
        
        # Draw and update the dropdown menu
        self.drop_down_button_solo.draw(self.screen)
        self.drop_down_button_solo.update(self.events)

        self.display_system_buttons()

        # Start button - Under the dropdown menu
        start_button = pygame.Rect(
            center_x - 150,
            dropdown_y + vertical_spacing * 3.5,  
            300,
            self.button_height
        )
        pygame.draw.rect(self.screen, (150, 255, 150), start_button)
        pygame.draw.rect(self.screen, self.BLACK, start_button, 2)
        start_text = self.body_font.render("Start Game", True, self.BLACK)
        start_rect = start_text.get_rect(center=start_button.center)
        self.screen.blit(start_text, start_rect)
        self.computer_buttons['start'] = (start_button, None)

        # Warning message - At the bottom
        warning_font = pygame.font.Font(None, 24)
        warning_text = "Note: The X-DEFENSIVE computer player might take a slightly longer time to decide on its actions because it carefully considers all possible scenarios!"
        warning_surface = warning_font.render(warning_text, True, self.BLACK)
        warning_rect = warning_surface.get_rect(center=(center_x, dropdown_y + vertical_spacing * 4.5))  
        self.screen.blit(warning_surface, warning_rect)

        selected_option_1 = self.drop_down_button_solo.selected

        if self.drop_down_button_1.option_list[selected_option_1] == "DEFENSIVE":
            self.player1 = RandomStrategyPlayer("Bowser")
        elif self.drop_down_button_1.option_list[selected_option_1] == "X-DEFENSIVE":
            self.player1 = ExpectationValueStrategyPlayer("Bowser")
        elif self.drop_down_button_1.option_list[selected_option_1] == "AGGRESSIVE":
            self.player1 = RulebasedStrategyPlayer("Bowser")
        elif self.drop_down_button_1.option_list[selected_option_1] == "X-AGGRESSIVE":
            self.player1 = ProbabilityStrategyPlayer("Bowser")



    def setup_screen_2(self):
        """Screen displayed when setting up the game"""
        center_x = self.width // 2
        center_y = self.height // 2
        vertical_spacing = 70  
        
        # Title - Higher up
        title_y = center_y - 300  
        self.title_rect = self.title.get_rect(center=(center_x, title_y))
        self.screen.blit(self.title, self.title_rect)

        # Subtitle - Under title
        subtitle = self.body_font.render("Please select opponents:", True, self.BLACK)
        subtitle_rect = subtitle.get_rect(center=(center_x, title_y + vertical_spacing))
        self.screen.blit(subtitle, subtitle_rect)

        # Profile pictures - Under subtitle, horizontally distributed
        profile_y = title_y + vertical_spacing * 3  
        profile_spacing = 400  # Horizontal spacing between two profile pictures
        
        # Save profile picture positions for click detection
        bowser_rect = self.player_profile['bowser'].get_rect(center=(center_x - profile_spacing//2, profile_y))
        peach_rect = self.player_profile['peach'].get_rect(center=(center_x + profile_spacing//2, profile_y))
        self.screen.blit(self.player_profile['bowser'], bowser_rect)
        self.screen.blit(self.player_profile['peach'], peach_rect)

        # Strategy selection dropdowns - Under profile pictures
        dropdown_y = profile_y + vertical_spacing * 1  
        dropdown_width = 300
        dropdown_height = self.button_height
        
        # Update the dropdown position
        self.drop_down_button_1.rect.x = center_x - profile_spacing//2 - 150
        self.drop_down_button_1.rect.y = dropdown_y
        
        self.drop_down_button_2.rect.x = center_x + profile_spacing//2 - 150
        self.drop_down_button_2.rect.y = dropdown_y
        
        # Draw and update the dropdown menu
        self.drop_down_button_1.draw(self.screen)
        self.drop_down_button_2.draw(self.screen)
        self.drop_down_button_1.update(self.events)
        self.drop_down_button_2.update(self.events)

        self.display_system_buttons()
        # Start button - Under the dropdown menu
        start_button = pygame.Rect(
            center_x - 150,
            dropdown_y + vertical_spacing * 3.6,
            300,
            self.button_height
        )
        pygame.draw.rect(self.screen, (150, 255, 150), start_button)
        pygame.draw.rect(self.screen, self.BLACK, start_button, 2)
        start_text = self.body_font.render("Start Game", True, self.BLACK)
        start_rect = start_text.get_rect(center=start_button.center)
        self.screen.blit(start_text, start_rect)
        self.computer_buttons['start'] = (start_button, None)

        # Warning message - At the bottom
        warning_font = pygame.font.Font(None, 24)
        warning_text = "Note: The X-DEFENSIVE computer player might take a slightly longer time to decide on its actions because it carefully considers all possible scenarios!"
        warning_surface = warning_font.render(warning_text, True, self.BLACK)
        warning_rect = warning_surface.get_rect(center=(center_x, dropdown_y + vertical_spacing * 4.5))
        self.screen.blit(warning_surface, warning_rect)

        selected_option_1 = self.drop_down_button_1.selected
        selected_option_2 = self.drop_down_button_2.selected

        if self.drop_down_button_1.option_list[selected_option_1] == "DEFENSIVE":
            self.player1 = RandomStrategyPlayer("Bowser")
        elif self.drop_down_button_1.option_list[selected_option_1] == "X-DEFENSIVE":
            self.player1 = ExpectationValueStrategyPlayer("Bowser")
        elif self.drop_down_button_1.option_list[selected_option_1] == "X-AGGRESSIVE":
            self.player1 = ProbabilityStrategyPlayer("Bowser")
        elif self.drop_down_button_1.option_list[selected_option_1] == "AGGRESSIVE":
            self.player1 = RulebasedStrategyPlayer("Bowser")

        if self.drop_down_button_2.option_list[selected_option_2] == "DEFENSIVE":
            self.player2 = RandomStrategyPlayer("Princess Peach")
        elif self.drop_down_button_2.option_list[selected_option_2] == "X-DEFENSIVE":
            self.player2 = ExpectationValueStrategyPlayer("Princess Peach")
        elif self.drop_down_button_2.option_list[selected_option_2] == "X-AGGRESSIVE":
            self.player2 = ProbabilityStrategyPlayer("Princess Peach")
        elif self.drop_down_button_2.option_list[selected_option_2] == "AGGRESSIVE":
            self.player2 = RulebasedStrategyPlayer("Princess Peach")


    def display_action_buttons(self):
        for action, rect in self.button_positions.items():    #Display all the action buttons
            if action == 'finish draw':                       #Display 'Finish Draw' button if currently drawing cards, otherwise don't display this button
                if self.turn_state['is_drawing']:
                    self.screen.blit(self.buttons[action], rect)
            else:
                self.screen.blit(self.buttons[action], rect)
            
            if action == 'draw':
                if self.turn_state['is_finished_drawing'] or self.turn_state['cards_drawn_count'] >= 3 or len(self.current_player.cards) + self.turn_state['cards_drawn_count'] >= self.MAX_HAND_SIZE or self.target_player:
                    self.screen.blit(self.buttons['draw_banned'], rect)
                else:
                    self.screen.blit(self.buttons['draw'], rect)

            if action == 'take':
                if self.turn_state['is_drawing'] or self.turn_state['has_taken'] or len(self.current_player.cards) >= self.MAX_HAND_SIZE or self.target_player:
                    self.screen.blit(self.buttons['take_banned'], rect)
                else:
                    self.screen.blit(self.buttons['take'], rect)

            if action == 'pass':
                if self.turn_state['has_drawn'] or self.turn_state['has_taken']:
                    self.screen.blit(self.buttons['pass_banned'], rect)
                else:
                    self.screen.blit(self.buttons['pass'], rect)

            if action == 'discard':
                if self.turn_state['is_drawing'] or not self.current_player.exist_valid_group() or not self.selected_cards or self.target_player:
                    self.screen.blit(self.buttons['discard_banned'], rect)
                else:
                    self.screen.blit(self.buttons['discard'], rect)

            if action == 'next':
                if self.turn_state['is_drawing'] or (not self.turn_state['has_drawn'] and not self.turn_state['has_taken'] and not self.turn_state['has_passed']) or self.target_player:
                    self.screen.blit(self.buttons['next_banned'], rect)
                else:
                    self.screen.blit(self.buttons['next'], rect)

            if action == 'computer_takeover':
                if self.turn_state['has_drawn'] or self.turn_state['has_taken'] or self.turn_state['has_passed'] or self.taken_turn_by_computer or self.target_player:
                    self.screen.blit(self.buttons['computer_takeover_banned'], rect)
                else:
                    self.screen.blit(self.buttons['computer_takeover'], rect)
                    
                    # If strategy buttons are displayed, draw them in order from top to bottom
                    if self.showing_computer_strategy_buttons:
                        for strategy in ['X-AGGRESSIVE', 'AGGRESSIVE', 'DEFENSIVE', 'X-DEFENSIVE']:
                            rect = self.computer_strategy_buttons[strategy]
                            pygame.draw.rect(self.screen, self.WHITE, rect)
                            pygame.draw.rect(self.screen, self.BLACK, rect, 2)
                            self.screen.blit(self.buttons[strategy], rect)
                    
                            # Add warning message when strategy buttons are shown
                            self.message = "Note: The X-DEFENSIVE computer player will take longer to decide on its actions because it carefully considers all possible scenarios!"


    def display_system_buttons(self):
        for action, rect in self.system_button_positions.items():  # Display all the action buttons
            '''
            if action == 'hint':
                # Display appropriate hint button based on state
                button_image = self.system_buttons['hint_on'] if self._hint_enabled else self.system_buttons['hint_off']
                self.screen.blit(button_image, rect)
            else:
            '''
            self.screen.blit(self.system_buttons[action], rect)


    def display_player_hand(self, player: Player, y_position: int):
        font = pygame.font.Font(None, 32)
        if player.is_human:
            if player == self.current_player:
                text = font.render(f"You", True, self.RED)
            elif player == self.target_player:
                text = font.render(f"You", True, self.WHITE)
            else:
                text = font.render(f"You", True, self.BLACK)
        else:
            if player == self.current_player:
                text = font.render(f"{player.name}", True, self.RED)
            elif player == self.target_player:
                text = font.render(f"{player.name}", True, self.WHITE)
            else:
                text = font.render(f"{player.name}", True, self.BLACK)
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

        message_font = pygame.font.Font(None, 28)
        turn_font = pygame.font.Font(None, 36)
        name_font = pygame.font.Font(None, 32)  # The font size used in display_player_hand
        
        # Calculate the position of the message area
        top_margin = int(self.height * 0.03)
        turn_text = f"Current Turn: {self.current_player.name}"
        turn_surface = turn_font.render(turn_text, True, self.BLACK) 
        turn_rect = turn_surface.get_rect(centerx=self.width // 2, top=top_margin)
        
        # Calculate the total height of the message area
        message_area_height = top_margin + turn_rect.height + 10 + (2 * 25)
        
        # Calculate the starting position of the computer player's hand
        computer_cards_start_y = message_area_height + 25

        # Get other players (not the current player)
        other_players = [p for p in self.players if p != self.current_player]
        
        # Calculate the maximum width of all player names
        max_text_width = max(
            name_font.render(f"{player.name}", True, self.BLACK).get_rect().width 
            for player in other_players
        )
        
        for player in other_players:
            # Find the X position of the player's name text
            text_x = self.CARD_LEFT_MARGIN
            # Find the Y position of this player's hand
            player_index = self.players.index(player)
            computer_index = sum(1 for p in self.players[:player_index] if not p.is_human)
            y_position = computer_cards_start_y + computer_index * 150
            
            name_text = name_font.render(f"{player.name}: ", True, self.BLACK)
            text_height = name_text.get_rect().height
            
            button_image = self.take_from_buttons[player.name]
            # Scale the button image to uniform width and text height
            scaled_button = pygame.transform.scale(button_image, (max_text_width + 20, text_height * 1.5))
            button_rect = scaled_button.get_rect()
            
            # Set the button position: Overlap with the player's name text
            button_rect.x = text_x
            button_rect.y = y_position - 40  
            
            self.player_select_buttons[player.name] = button_rect
            self.screen.blit(scaled_button, button_rect)


    def display_valid_groups_panel(self):
        """Display all current valid groups in a panel"""
        if not self.current_player.exist_valid_group():
            return

        left_margin = 20  
        panel_width = 400
        panel_x = left_margin

        computer_cards_start_y = self.height * 0.03 + 60  
        last_computer_y = computer_cards_start_y + (len([p for p in self.players if not p.is_human]) - 1) * 150
        last_computer_cards_height = 90  

        human_cards_y = self.height - 200  

        available_height = human_cards_y - (last_computer_y + last_computer_cards_height)
        panel_y = last_computer_y + last_computer_cards_height + (available_height * 0.2)  

        title_font = pygame.font.Font(None, 28)
        text_font = pygame.font.Font(None, 22)
        
        title = "Current Valid Groups"
        title_text = title_font.render(title, True, self.BLACK)
        title_y = panel_y + 8
        self.screen.blit(title_text, (panel_x + 10, title_y))

        y = title_y + 30
        line_height = 16  
        
        valid_groups = self.current_player.all_valid_groups()
        # Limit the number of valid groups displayed to 18
        max_groups = min(18, len(valid_groups))
        
        for i, group in enumerate(valid_groups[:max_groups]):
            group_desc = ', '.join(f"{card.color} {card.number}" for card in group)
            group_text = text_font.render(f"{i + 1}. {group_desc}", True, self.BLACK)
            self.screen.blit(group_text, (panel_x + 20, y))
            y += line_height
        
        # If there are more valid groups, display the remaining groups count
        if len(valid_groups) > max_groups:
            remaining = len(valid_groups) - max_groups
            more_text = text_font.render(f"...and {remaining} more groups", True, self.BLACK)
            self.screen.blit(more_text, (panel_x + 20, y))


    def update_hint_calculations(self):
        """Only update the calculation results of hint information at specific times"""
        '''
        # Add early return if hints are disabled
        if not self._hint_enabled:
            self._hint_probabilities = {}
            self._hint_expectations = {}
            return
        '''
            
        if not self.current_player or not self.current_player.is_human or self.taken_turn_by_computer:
            return

        # If there is a valid group, no need to calculate probabilities and expectations
        if self.current_player.exist_valid_group():
            self._hint_probabilities = {}
            self._hint_expectations = {}
            return

        game_state = {
            'current_player': self.current_player,
            'other_players': [p for p in self.players if p != self.current_player],
            'deck_cards': self.deck,
            'deck_size': len(self.deck)
        }
        
        # Determine which hint information to calculate based on the current state
        if not self.turn_state['is_finished_drawing'] and not self.turn_state['has_taken']:
            self._hint_probabilities = self.current_player.calculate_probability(game_state)
            #draw_exp = {}
            #take_exp = {}
            draw_exp = self.current_player.draw_expectation(game_state)
            take_exp = self.current_player.take_expectation(game_state)
            self._hint_expectations = {**draw_exp, **take_exp}
        elif self.turn_state['is_finished_drawing'] and not self.turn_state['has_taken']:
            self._hint_probabilities = {k: v for k, v in self.current_player.calculate_probability(game_state).items() 
                                    if k[0] == 'take'}
            self._hint_expectations = self.current_player.take_expectation(game_state)
        elif self.turn_state['has_taken'] and not self.turn_state['is_finished_drawing']:
            self._hint_probabilities = {k: v for k, v in self.current_player.calculate_probability(game_state).items() 
                                    if k[0] == 'draw'}
            self._hint_expectations = self.current_player.draw_expectation(game_state)
        else:
            self._hint_probabilities = {}
            self._hint_expectations = {}


    def display_hint_panel(self):
        '''
        if not self._hint_enabled:
            return
        '''
            
        if not self.current_player or not self.current_player.is_human or self.taken_turn_by_computer:
            return
        
        right_margin = 20
        panel_x = self.width - 450 - right_margin 

        computer_cards_start_y = self.height * 0.03 + 60
        last_computer_y = computer_cards_start_y + (len([p for p in self.players if not p.is_human]) - 1) * 150
        last_computer_cards_height = 90
        
        human_cards_y = self.height - 200
        
        available_height = human_cards_y - (last_computer_y + last_computer_cards_height)
        panel_y = last_computer_y + last_computer_cards_height + (available_height * 0.2)
        
        hint_font = pygame.font.Font(None, 28)
        text_font = pygame.font.Font(None, 22)
        
        title = hint_font.render("Hint", True, self.BLACK)
        title_y = panel_y + 8
        self.screen.blit(title, (panel_x + 10, title_y))

        #If there is a valid group, find the best discard combination and display it
        if self.current_player.exist_valid_group():
            best_discard = self.current_player.find_best_discard()
            if best_discard:
                y = title_y + 30
                line_height = 16
                
                text = text_font.render("Best discard combination:", True, self.BLACK)
                self.screen.blit(text, (panel_x + 10, y))
                y += line_height + 3
                
                for group in best_discard:
                    cards_text = ", ".join(str(card) for card in group)
                    text = text_font.render(cards_text, True, self.BLACK)
                    self.screen.blit(text, (panel_x + 20, y))
                    y += line_height
            return
            
        # If there is no valid group, display probabilities and expectations of each action
        if not hasattr(self, '_hint_probabilities') or not hasattr(self, '_hint_expectations'):
            return
            
        if not self._hint_probabilities and not self._hint_expectations:
            return
        
        # Custom sorting function
        def action_sort_key(action):
            action_type, count_or_none, player_or_none = action
            if action_type == 'draw':
                return (0, count_or_none or 0) 
            elif action_type == 'take':
                return (1, player_or_none.name)  
            else:  #Pass operation
                return (2, 0)
        
        y = title_y + 40
        line_height = 16  
        
        if self._hint_probabilities:
            text = text_font.render("Probability of obtaining a valid group:", True, self.BLACK)
            self.screen.blit(text, (panel_x + 10, y))
            y += line_height + 3  
            
            for action in sorted(self._hint_probabilities.keys(), key=action_sort_key):
                action_type, count_or_none, player_or_none = action
                if action_type == 'draw':
                    text = f"draw {count_or_none} cards: {self._hint_probabilities[action]:.2%}"
                elif action_type == 'take':
                    text = f"take 1 card from {player_or_none.name}: {self._hint_probabilities[action]:.2%}"
                elif action_type == 'pass':
                    continue  
                text = text_font.render(text, True, self.BLACK)
                self.screen.blit(text, (panel_x + 20, y))
                y += line_height
        
        if self._hint_expectations:
            y += line_height
            text = text_font.render("Expected value of the number of hand cards to be reduced:", True, self.BLACK)
            self.screen.blit(text, (panel_x + 10, y))
            y += line_height + 3  
            
            for action in sorted(self._hint_expectations.keys(), key=action_sort_key):
                action_type, count_or_none, player_or_none = action
                if action_type == 'draw':
                    text = f"draw {count_or_none} cards: {self._hint_expectations[action]:.2f}"
                elif action_type == 'take':
                    text = f"take 1 card from {player_or_none.name}: {self._hint_expectations[action]:.2f}"
                elif action_type == 'pass':
                    continue  
                text = text_font.render(text, True, self.BLACK)
                self.screen.blit(text, (panel_x + 20, y))
                y += line_height


    def show_game_over_popup(self, winner: Player):
        """If one player wins, display a popup"""
        popup_width = 800
        popup_height = 200
        popup_x = (self.width - popup_width) // 2
        popup_y = (self.height - popup_height) // 2

        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(self.screen, self.WHITE, popup_rect)
        pygame.draw.rect(self.screen, self.BLACK, popup_rect, 2)

        font = pygame.font.Font(None, 48)

        if winner.is_human:
            self.game_win_sound.play()
            winner_text = f"Congratulations! You win"
            text_surface = font.render(winner_text, True, self.BLACK)
            text_rect = text_surface.get_rect(centerx=self.width // 2, centery=self.height // 2 - 40)
            self.screen.blit(text_surface, text_rect)
        else:
            self.game_lose_sound.play()
            winner_text = f"You lose! {winner.name} wins!"
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

                break


    def select_no_of_players(self, pos: Tuple[int, int]):
        """Human player clicks on the setup screen"""
        for name, (rect, computer_player) in self.computer_buttons.items():
            if rect.collidepoint(pos):
                if name == '2 Players':
                    self.no_of_player = 2
                    self.game_phase = GamePhase.SETUP
                elif name == '3 Players':
                    self.no_of_player = 3
                    self.game_phase = GamePhase.SETUP
                break


    def click_in_game(self, pos: Tuple[int, int]):
        """Human player clicks buttons on the game screen"""
        if (not self.current_player.is_human) or (
                self.taken_turn_by_computer and not self.temp_computer_finished):  # If it is not human player's turn or temporary computer player has not finished its operations, do not allow human player to click buttons
            return

        clicked_button = None
        clicked_player_button = None
        clicked_strategy_button = None

        for action, rect in self.button_positions.items():  # Check if human player clicked on any action button
            if rect.collidepoint(pos):
                clicked_button = action
                break

        if self.showing_computer_strategy_buttons:  # Check if human player clicked on any strategy button
            for strategy, rect in self.computer_strategy_buttons.items():
                if rect.collidepoint(pos):
                    self.showing_player_select_buttons = False
                    self.turn_state['waiting_for_take'] = False
                    clicked_strategy_button = strategy
                    break

            if not clicked_strategy_button and clicked_button != 'computer_takeover':  # Hide strategy buttons if clicked anywhere else except strategy buttons and computer_takeover
                self.showing_computer_strategy_buttons = False
                self.message = ""
                if clicked_button:
                    if clicked_button != 'take':
                        self.showing_player_select_buttons = False
                        self.turn_state['waiting_for_take'] = False

                    if clicked_button == 'finish draw':
                        if self.turn_state['is_drawing']:
                            self.human_finish_drawing()
                    elif clicked_button == 'draw':
                        self.human_draw()
                    elif clicked_button == 'take':
                        self.human_select_take()
                    elif clicked_button == 'pass':
                        self.human_pass()
                    elif clicked_button == 'discard':
                        self.human_discard()
                    elif clicked_button == 'next':
                        self.human_start_next_turn()
                    return
                else:
                    return

        if self.showing_player_select_buttons:  # Check if human player clicked on any player select button
            for player_name, button_rect in self.player_select_buttons.items():
                if button_rect.collidepoint(pos):
                    clicked_player_button = player_name
                    break

        if clicked_button == 'computer_takeover':  # if clicked on computer_takeover button
            if self.turn_state['has_drawn'] or self.turn_state['has_taken'] or self.turn_state['has_passed']:
                self.message = "Cannot let computer take over - You have already taken operations this turn"
            else:
                self.showing_player_select_buttons = False
                self.turn_state['waiting_for_take'] = False
                self.showing_computer_strategy_buttons = True
            return

        if clicked_strategy_button:
            self.let_computer_take_turn(clicked_strategy_button)
            return

        if self.showing_player_select_buttons:  # If human player clicked on any player select button
            if clicked_player_button:
                for player in self.players:
                    if player.name == clicked_player_button:
                        self.target_player = player
                        self.showing_player_select_buttons = False
                        self.human_take(self.target_player)
                        return

        if clicked_button:  # If clicked on any action button, take actions accordingly
            if clicked_button != 'take':
                self.showing_player_select_buttons = False
                self.turn_state['waiting_for_take'] = False

            if clicked_button == 'finish draw':
                if self.turn_state['is_drawing']:
                    self.human_finish_drawing()
            elif clicked_button == 'draw':
                self.human_draw()
            elif clicked_button == 'take':
                self.human_select_take()
            elif clicked_button == 'pass':
                self.human_pass()
            elif clicked_button == 'discard':
                self.human_discard()
            elif clicked_button == 'next':
                self.human_start_next_turn()
            return

        if not self.turn_state[
            'waiting_for_take']:  # When not waiting for taking a card, handle card clicking means selecting cards to discard
            self.click_card(pos)

    def system_actions_in_game(self, pos: Tuple[int, int]):
        """Human player clicks buttons on the game screen"""
        clicked_button = None

        for action, rect in self.system_button_positions.items():  # Check if human player clicked on any action button
            if rect.collidepoint(pos):
                '''
                if action == 'hint':
                    self._hint_enabled = not self._hint_enabled
                    if not self._hint_enabled:
                        self._hint_probabilities = {}
                        self._hint_expectations = {}
                    return
                '''
                clicked_button = action
                break

        if clicked_button == "restart":
            self.game_phase = GamePhase.WELCOME
        if clicked_button == "quit":
            pygame.quit()
        if clicked_button == 'music':
            self.bgm_switch = not self.bgm_switch
            self.background_music_control()

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
        
        if self.turn_state['waiting_for_take'] and self.target_player:
            for card in self.target_player.cards:
                card.hover = False
            
            for card in self.target_player.cards:
                if card.contains_point(pos):
                    card.hover = True
                    break
        else:                                           #Normal case check current player's cards
            for card in self.current_player.cards:
                card.hover = False

            for card in self.current_player.cards:
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

        if len(self.current_player.cards) + self.turn_state['cards_drawn_count'] >= self.MAX_HAND_SIZE:
            self.message = f"Cannot draw - already has {self.MAX_HAND_SIZE} cards"
            return
        self.card_draw_sound.play()
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
        
        self.turn_state['is_finished_drawing'] = True

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
        self.update_hint_calculations()

    def human_select_take(self):
        if self.turn_state['is_drawing']:
            self.message = "Cannot take - please finish drawing cards first"
            return

        if self.turn_state['has_taken']:
            self.message = "Cannot take - already took a card this turn"
            return

        if len(self.current_player.cards) >= self.MAX_HAND_SIZE:
            self.message = f"Cannot take - hand already has {self.MAX_HAND_SIZE} cards"
            return

        self.showing_player_select_buttons = True
        self.turn_state['waiting_for_take'] = True
        self.message = "Select a player to take one card from"


    def human_take(self, target_player: Player):
        if not self.turn_state['waiting_for_take'] or not target_player:
            return

        self.hand_card_shuffle_sound.play()
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
        
        self.taken_card = None
        self.message = "Click a card to take"
        
        while self.turn_state['waiting_for_take']:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    clicked_button = None                  #First check whether user clicks on some action buttons
                    for action, rect in self.button_positions.items():
                        if rect.collidepoint(event.pos):
                            clicked_button = action
                            break
                    
                    if clicked_button:
                        self.message = "Cannot perform other actions - please first click one card to take"
                        continue  
                    
                    self.click_card(event.pos)        #If not clicking on any action button, handle card clicking
                elif event.type == pygame.MOUSEMOTION:
                    self.card_hover(event.pos)
        
            self.update_screen()
            self.clock.tick(self.FPS)
        
        if self.taken_card:
            self.turn_state['has_taken'] = True
            self.turn_state['waiting_for_take'] = False

            self.taken_card.face_down = False                                          #Set the taken card to face up after human player clicks on it
            original_pos = (self.taken_card.rect.x, self.taken_card.rect.y)            #The original position and the target position (temporary display area) of the taken card animation
            temp_display_pos = (self.CARD_LEFT_MARGIN, self.current_player.cards[0].rect.y) 
            
            target_player.cards.remove(self.taken_card)                              #Remove the taken card from target player's hand
            self.taken_card.reset_state()                                             #Reset the state of the taken card to default

            self.card_draw_sound.play()
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
            self.showing_player_select_buttons = False
            self.player_select_buttons.clear()

            self.message = f"{self.current_player.name} took {self.taken_card.color} {self.taken_card.number} from {target_player.name}"

            if len(target_player.cards) == 0:                                       #If target player has no cards left, game over
                self.game_phase = GamePhase.GAME_OVER
                self.message = f"{target_player.name} wins!"
                self.update_screen()
                self.show_game_over_popup(target_player)
            
            for card in target_player.cards:                                        #Flip back the remaining cards in target player's hand
                card.face_down = False
                card.update()
            
            self.taken_card = None
            self.target_player = None

            animation_frames = 0                                                           #Final animation to complete card positioning
            while animation_frames < 35:
                self.screen.fill(self.BACKGROUND_COLOR)
                self.screen.blit(self.background, (0, 0))
                self.game_screen(draw_temp_cards=False)
                
                for card in self.current_player.cards:
                    card.update()
                self.update_screen()
                
                animation_frames += 1
                self.clock.tick(40)
            
            self.check_and_display_valid_groups()                                    #Check and display valid groups after taking
            self.update_hint_calculations()


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

            self.card_draw_sound.play()

            self.card_animation.discard_card_animation(                            #Animate the discarding of the selected cards
                card, start_pos, target_pos, self.game_screen
            )
            
            card.reset_state()
            self.deck.append(card)

        random.shuffle(self.deck)
        self.card_shuffle_sound.play()
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
            self.show_game_over_popup(self.current_player)
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

        self.update_hint_calculations()


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

        if not self.turn_state['has_drawn'] and not self.turn_state['has_taken'] and not self.turn_state['has_passed'] and not len(self.current_player.cards) >= self.MAX_HAND_SIZE:
            self.message = "You must take an action before starting next turn"
            return
        
        self.taken_turn_by_computer = False
        self.temp_computer = None
        self.temp_computer_finished = False
        self.selected_cards = []
        self.turn_state = self.initial_turn_state()
        current_index = self.players.index(self.current_player)                      #Get the index of the current player
        self.current_player = self.players[(current_index + 1) % len(self.players)]  #Set the player with the next index as the current player
        self.message = f"{self.current_player.name}'s turn"


    def check_and_display_valid_groups(self) -> bool:
        if self.current_player.exist_valid_group():
            if self.current_player.is_human:
                if self.taken_turn_by_computer:
                    self.message = f"You have valid groups! {self.temp_computer.get_strategy_name()} computer player will help you discard"
                else:
                    self.message = "You have valid groups! Select cards and click Discard to remove them"
                return True
            else:
                self.message = f"{self.current_player.name} has valid groups!"
                self.update_screen()
                pygame.time.wait(500)
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


    def let_computer_take_turn(self, strategy: str):
        """Let computer take over the current turn with specified strategy"""
        self.showing_computer_strategy_buttons = False
        self.taken_turn_by_computer = True
        self.temp_computer_finished = False
        
        if strategy == 'DEFENSIVE':       # Create temporary computer player with the same cards as human player
            self.temp_computer = RandomStrategyPlayer("Temp Computer")
        elif strategy == 'X-DEFENSIVE':
            self.temp_computer = ExpectationValueStrategyPlayer("Temp Computer")
        elif strategy == 'X-AGGRESSIVE':
            self.temp_computer = ProbabilityStrategyPlayer("Temp Computer")
        elif strategy == 'AGGRESSIVE':
            self.temp_computer = RulebasedStrategyPlayer("Temp Computer")
              
        self.temp_computer.cards = self.current_player.cards.copy() 
               
        game_state = {
            'current_player': self.current_player,
            'other_players': [p for p in self.players if p != self.current_player],
            'deck_cards': self.deck,
            'deck_size': len(self.deck)
        }
        
        self.message = f"{self.temp_computer.get_strategy_name()} computer player is helping you take this turn..."
        self.update_screen()
        pygame.time.wait(500)
        
        if self.check_and_display_valid_groups():
            self.computer_discard()

        if len(self.current_player.cards) >= self.MAX_HAND_SIZE:     
            self.message = f"You have reached maximum hand size ({self.MAX_HAND_SIZE} cards), passing turn"
            self.update_screen()
            pygame.time.wait(1000)
            self.human_start_next_turn()
            return

        action, draw_count, target_player = self.temp_computer.choose_first_action(game_state)
        
        if action == 'draw':
            self.computer_draw(draw_count)
            self.turn_state['has_drawn'] = True
            self.temp_computer.cards = self.current_player.cards.copy()
        elif action == 'take':
            self.computer_take(target_player)
            self.turn_state['has_taken'] = True
            self.temp_computer.cards = self.current_player.cards.copy()
        elif action == 'pass':
            self.turn_state['has_passed'] = True
            self.message = f"{self.temp_computer.get_strategy_name()} computer player helps you choose to pass"
            self.temp_computer_finished = True
            self.update_screen()
            pygame.time.wait(800)
            self.message = f"{self.temp_computer.get_strategy_name()} computer player has finished helping you take this turn, click 'Next' to continue"
            self.update_screen()
            return

        if type(self.temp_computer) == ExpectationValueStrategyPlayer:
            self.message = f"{self.temp_computer.get_strategy_name()} computer player is thinking about the next action..."
            self.update_screen()
        
        action, draw_count, target_player = self.temp_computer.choose_second_action(game_state, action)
        
        if action == 'draw':
            self.computer_draw(draw_count)
            self.turn_state['has_drawn'] = True
            self.temp_computer.cards = self.current_player.cards.copy()           
        elif action == 'take':
            self.computer_take(target_player)
            self.turn_state['has_taken'] = True
            self.temp_computer.cards = self.current_player.cards.copy()
        elif action == 'pass':
            self.turn_state['has_passed'] = True
        
        self.temp_computer_finished = True
        self.message = f"{self.temp_computer.get_strategy_name()} computer player has finished helping you take this turn, click 'Next' to continue"
        self.update_screen()


    def computer_turn(self):
        pygame.time.wait(500)

        if self.check_and_display_valid_groups():
            self.computer_discard()

        if len(self.current_player.cards) >= self.MAX_HAND_SIZE:     # Check if the current computer player has reached the maximum hand size. If so, pass turn.
            self.message = f"{self.current_player.name} has reached maximum hand size ({self.MAX_HAND_SIZE} cards), passing turn"
            self.update_screen()
            pygame.time.wait(1000)
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

        action, draw_count, target_player = self.current_player.choose_first_action(game_state)

        if action == 'draw':
            self.computer_draw(draw_count)
            
        elif action == 'take':
            self.computer_take(target_player)

        elif action == 'pass':
            self.message = f"{self.current_player.name} chooses to pass"
            self.update_screen()
            pygame.time.wait(800)
            self.computer_start_next_turn()
            return
        
        if type(self.current_player) == ExpectationValueStrategyPlayer:
            self.message = f"{self.current_player.name} is thinking about the next action..."
            self.update_screen()
        
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
        if self.current_player.is_human:
            self.message = f"{self.temp_computer.get_strategy_name()} computer player decided to help you take a card from {target_player.name}"
        else:
            self.message = f"{self.current_player.name} decided to take a card from {target_player.name}"
        self.update_screen()
        pygame.time.wait(800)

        self.hand_card_shuffle_sound.play()
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
        self.card_draw_sound.play()
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
        if self.current_player.is_human:
            self.message = f"{self.temp_computer.get_strategy_name()} computer player helps you took {taken_card.color} {taken_card.number} from {target_player.name}"
        else:
            self.message = f"{self.current_player.name} took {taken_card.color} {taken_card.number} from {target_player.name}"

        if len(target_player.cards) == 0:
            self.game_phase = GamePhase.GAME_OVER
            self.message = f"{target_player.name} wins!"
            self.update_screen()
            self.show_game_over_popup(target_player)

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
            pygame.time.wait(200)

        self.update_screen()


    def computer_draw(self, draw_count: int):
        if self.current_player.is_human:
            self.message = f"{self.temp_computer.get_strategy_name()} computer player decided to help you draw from deck"
        else:
            self.message = f"{self.current_player.name} decided to draw from deck"
        self.update_screen()
        pygame.time.wait(800)

        for i in range(draw_count):
            if len(self.current_player.cards) + i > self.MAX_HAND_SIZE:
                if self.current_player.is_human:
                    self.message = f"You have reached maximum hand size ({self.MAX_HAND_SIZE} cards)"
                else:
                    self.message = f"{self.current_player.name} has reached maximum hand size"
                self.update_screen()
                return

            card = self.deck.pop()
            self.card_draw_sound.play()

            start_pos = (self.deck_area.x + min(5, len(self.deck)) * 2,
                         self.deck_area.y + min(5, len(self.deck)) * 2)
            target_pos = (self.temp_draw_area.x + self.turn_state['cards_drawn_count'] * 20,
                         self.temp_draw_area.y + self.turn_state['cards_drawn_count'] * 2)

            self.card_animation.draw_to_temp_draw_area(start_pos, target_pos, self.game_screen)

            self.turn_state['drawn_cards'].append(card)
            self.turn_state['cards_drawn_count'] += 1
            self.turn_state['is_drawing'] = True
            
            if self.current_player.is_human:
                self.message = f"{self.temp_computer.get_strategy_name()} computer player has drew {self.turn_state['cards_drawn_count']} cards"
            else:
                self.message = f"{self.current_player.name} has drew {self.turn_state['cards_drawn_count']} cards"

            if self.turn_state['cards_drawn_count'] == 3:
                self.message += " (reached maximum draw limit 3 for this turn)"
            else:
                self.message += f" ({3 - self.turn_state['cards_drawn_count']} draws remaining)"
            pygame.time.wait(300)

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
        
        if self.current_player.is_human:
            self.message = f"{self.temp_computer.get_strategy_name()} computer player finished helping you draw cards"
        else:
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
            pygame.time.wait(200)

        self.update_screen()


    def computer_discard(self):
        if self.current_player.exist_valid_group():
            groups_to_discard = self.current_player.find_best_discard()

        if groups_to_discard:
            i = 0
            for group in groups_to_discard:
                self.highlight_computer_valid_groups(group)
                self.update_screen()
                pygame.time.wait(300)

                index_order_dict = dict(zip(range(0, 10), ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"])) 

                if self.current_player.is_human:
                    self.message = f"{self.temp_computer.get_strategy_name()} computer player decided to help you to {index_order_dict[i]} discard group: {', '.join(f'{card.color} {card.number}' for card in group)}"
                else:
                    self.message = f"{self.current_player.name} decided to {index_order_dict[i]} discard group: {', '.join(f'{card.color} {card.number}' for card in group)}"

                CARDS_DELAY = 5
                
                for card_index, card in enumerate(group):
                    self.current_player.remove_card(card)
                    start_pos = (card.rect.x, card.rect.y)
                    target_pos = (self.deck_area.x + min(5, len(self.deck)) * 2, 
                         self.deck_area.y + min(5, len(self.deck)) * 2)

                    for _ in range(card_index * CARDS_DELAY):
                        self.update_screen()
                        self.clock.tick(self.FPS)
                    self.card_draw_sound.play()
                    self.card_animation.discard_card_animation(
                        card, start_pos, target_pos, self.game_screen
                    )
                    
                    card.reset_state()
                    self.deck.append(card)

                random.shuffle(self.deck)
                self.card_shuffle_sound.play()
                self.card_animation.shuffle_animation(
                    self.deck_area,
                    redraw_game_screen=self.game_screen
                )
                
                if self.current_player.is_human:
                    self.message = f"{self.temp_computer.get_strategy_name()} computer player helps you discarded group: {', '.join(f'{card.color} {card.number}' for card in group)}"
                else:
                    self.message = f"{self.current_player.name} discarded group: {', '.join(f'{card.color} {card.number}' for card in group)}"
                
                animation_frames = 0                                 #Wait for the remaining cards to animate to their new positions
                while animation_frames < 30:
                    for card in self.current_player.cards:
                        card.update()
                    
                    self.update_screen()
                    animation_frames += 1
                    self.clock.tick(self.FPS)
                
                pygame.time.wait(300)

                if len(self.current_player.cards) == 0:
                    self.game_phase = GamePhase.GAME_OVER
                    self.message = f"{self.current_player.name} wins!"
                    self.update_screen()
                    self.show_game_over_popup(self.current_player)
                else:
                    i += 1
                    self.update_screen()
                    pygame.time.wait(300)


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
        pygame.time.wait(500)


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
        if self.current_player.is_human:
            self.update_hint_calculations()
        self.check_and_display_valid_groups()

    
    def get_deck_positions(self):
        """
        Generate the initial positions of cards in the deck.
        :return: List of positions for cards in the deck
        """
        return [(self.width // 2, self.height // 2)] * len(self.players)


    def start_game(self, selected_computers: List[ComputerPlayer]):
        self.players = [Player("Human Player", is_human=True)]
        self.players.extend(selected_computers)

        for player in self.players:
            for _ in range(self.INITIAL_HAND_SIZE):
                if self.deck:
                    player.add_card(self.deck.pop())

        self.current_player = self.players[0]
        self.game_phase = GamePhase.PLAYER_TURN
        self.message = "Game started!"
        self.turn_state = self.initial_turn_state()

        num_players = len(self.players)
        if num_players == 2:
            self.card_animation.deal_cards_with_trailing_effect(
            self.get_deck_positions(),
            self.card_animation.get_two_players_positions()
        )
        elif num_players == 3:
            self.card_animation.deal_cards_with_trailing_effect(
            self.get_deck_positions(),
            self.card_animation.get_three_players_positions()
            )
        else:
            raise ValueError("Only 2 or 3 players are supported!")

    # Update screen after animations
        self.update_screen()

        self.update_hint_calculations()

        self.check_and_display_valid_groups()
        


    def run(self):
        running = True
        while running:
            self.events = pygame.event.get()
            for event in self.events:
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE: #Window size change event
                    self.width = event.w
                    self.height = event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    
                    button_width = 120
                    button_height = 50  
                    button_spacing = 20
                    center_buttons = ['finish draw', 'draw', 'take', 'discard', 'pass']
                    total_center_buttons = len(center_buttons)
                    total_center_width = (button_width * total_center_buttons) + (button_spacing * (total_center_buttons - 1))
                    
                    center_start_x = (self.width - total_center_width) // 2
                    bottom_y = self.height - button_height - 20
                    
                    self.button_positions = {
                        'computer_takeover': pygame.Rect(20, bottom_y, button_width, button_height),
                        
                        'finish draw': pygame.Rect(center_start_x, bottom_y, button_width, button_height),
                        'draw': pygame.Rect(center_start_x + (button_width + button_spacing), bottom_y, button_width, button_height),
                        'take': pygame.Rect(center_start_x + (button_width + button_spacing) * 2, bottom_y, button_width, button_height),
                        'discard': pygame.Rect(center_start_x + (button_width + button_spacing) * 3, bottom_y, button_width, button_height),
                        'pass': pygame.Rect(center_start_x + (button_width + button_spacing) * 4, bottom_y, button_width, button_height),
                        
                        'next': pygame.Rect(self.width - button_width - 20, bottom_y, button_width, button_height)
                    }
                    
                    strategy_button_spacing = button_height + 5  
                    self.computer_strategy_buttons = {
                        'X-AGGRESSIVE': pygame.Rect(
                            20,
                            bottom_y - (button_height + strategy_button_spacing) * 4,
                            button_width,
                            button_height
                        ),
                        'AGGRESSIVE': pygame.Rect(
                            20,
                            bottom_y - (button_height + strategy_button_spacing) * 3,
                            button_width,
                            button_height
                        ),
                        'DEFENSIVE': pygame.Rect(
                            20,
                            bottom_y - (button_height + strategy_button_spacing) * 2,
                            button_width,
                            button_height
                        ),
                        'X-DEFENSIVE': pygame.Rect(
                            20,
                            bottom_y - (button_height + strategy_button_spacing),
                            button_width,
                            button_height
                        )
                    }
                    
                    background_image = pygame.image.load(os.path.join('backgrounds', 'background.png'))
                    self.background = pygame.transform.scale(background_image, (self.width, self.height))
                    
                    system_button_size = 40
                    system_button_margin = 20
                    system_button_top = 20
                    
                    self.system_button_positions = {
                        'quit': pygame.Rect(
                            self.width - system_button_size - system_button_margin, 
                            system_button_top, 
                            system_button_size, 
                            system_button_size
                        ),
                        'restart': pygame.Rect(
                            self.width - (system_button_size + system_button_margin) * 2, 
                            system_button_top, 
                            system_button_size, 
                            system_button_size
                        ),
                        'music': pygame.Rect(
                            self.width - (system_button_size + system_button_margin) * 3, 
                            system_button_top, 
                            system_button_size, 
                            system_button_size
                        )
                    }
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.system_actions_in_game(event.pos)  
                    
                    if self.game_phase == GamePhase.WELCOME:
                        self.select_no_of_players(event.pos)
                    elif self.game_phase == GamePhase.SETUP:
                        self.click_on_setup(event.pos)
                    elif self.game_phase == GamePhase.PLAYER_TURN:
                        self.click_in_game(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    if self.game_phase == GamePhase.PLAYER_TURN:
                        self.card_hover(event.pos)

            self.screen.fill(self.BACKGROUND_COLOR)
            self.screen.blit(self.background, (0, 0))

            if self.game_phase == GamePhase.WELCOME:
                self.welcome_screen()
            elif self.game_phase == GamePhase.SETUP:
                if self.no_of_player == 2:
                    self.selected_computers = [self.player1]
                    self.setup_screen_solo()
                elif self.no_of_player == 3:
                    self.selected_computers = [self.player1,self.player2]
                    self.setup_screen_2()
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
