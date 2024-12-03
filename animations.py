from player import Player
import pygame
from card import Card
from typing import List, Tuple

class CardAnimation:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, 
                 card_back: pygame.Surface, background: pygame.Surface,
                 background_color: Tuple[int, int, int],
                 card_width: int, card_height: int, game=None):
        self.screen = screen
        self.clock = clock
        self.card_back = card_back
        self.background = background
        self.background_color = background_color
        self.FPS = 120
        self.card_width = card_width
        self.card_height = card_height
        self.game = game


    def shuffle_animation(self, deck_area: pygame.Rect, redraw_game_screen=None, num_cards: int = 20, rounds: int = 2):
        """Cards shuffling animation"""
        for _ in range(rounds):
            self._split_cards_animation(deck_area.x, deck_area.y, 30, num_cards, None, redraw_game_screen)
            self._merge_cards_animation(deck_area.x, deck_area.y, 30, num_cards, None, redraw_game_screen)


    def _split_cards_animation(self, center_x: int, center_y: int, frames: int, 
                         num_cards: int, target_player=None, redraw_game_screen=None):
        """Cards splitting during shuffling"""
        for frame in range(frames):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            
            if target_player and redraw_game_screen:
                temp_cards = target_player.cards.copy()
                target_player.cards = []
                redraw_game_screen()
                target_player.cards = temp_cards
            elif redraw_game_screen:
                redraw_game_screen()
            
            progress = frame / frames
            offset = int(50 * progress)
            
            # Left pile
            for i in range(num_cards // 2):
                x = center_x - offset - (num_cards // 4 - i) * 2
                y = center_y + i * 2
                self.screen.blit(self.card_back, (x, y))
            
            # Right pile
            for i in range(num_cards // 2, num_cards):
                x = center_x + offset + (i - num_cards // 2) * 2
                y = center_y + (i - num_cards // 2) * 2
                self.screen.blit(self.card_back, (x, y))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)


    def _merge_cards_animation(self, center_x: int, center_y: int, frames: int, 
                         num_cards: int, target_player=None, redraw_game_screen=None):
        """Cards merging during shuffling"""
        for frame in range(frames):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            
            if target_player and redraw_game_screen:
                temp_cards = target_player.cards.copy()
                target_player.cards = []
                redraw_game_screen()
                target_player.cards = temp_cards
            elif redraw_game_screen:
                redraw_game_screen()
            
            progress = frame / frames
            offset = int(50 * (1 - progress))
            
            for i in range(num_cards):
                if i % 2 == 0:
                    x = center_x - offset + int(offset * 2 * progress) + i * 2
                    y = center_y + i * 2 + int(10 * (1 - progress))
                else:
                    x = center_x + offset - int(offset * 2 * progress) + i * 2
                    y = center_y + i * 2 - int(10 * (1 - progress))
                self.screen.blit(self.card_back, (x, y))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)
            

    def draw_to_temp_draw_area(self, start_pos: Tuple[int, int], target_pos: Tuple[int, int], 
                         redraw_game_screen) -> None:
        """Card moving from deck to temporary draw area"""
        animation_frames = 0
        max_frames = 15
        
        while animation_frames < max_frames:
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            
            progress = animation_frames / max_frames
            smooth_progress = (1 - (1 - progress) * (1 - progress))
            
            current_x = start_pos[0] + (target_pos[0] - start_pos[0]) * smooth_progress
            current_y = start_pos[1] + (target_pos[1] - start_pos[1]) * smooth_progress
            
            redraw_game_screen()
            self.screen.blit(self.card_back, (int(current_x), int(current_y)))
            
            pygame.display.flip()
            animation_frames += 1
            self.clock.tick(self.FPS)


    def flip_cards_animation(self, cards: List[Card], positions: List[Tuple[int, int]], 
                           redraw_game_screen) -> None:
        """Card flipping animation in temporary draw area"""
        animation_frames = 0
        while animation_frames < 10:
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            for (card, pos) in zip(cards, positions):
                x, y = pos
                progress = animation_frames / 20
                if progress < 0.5:
                    width = int(self.card_width * (1 - progress * 2))
                    if width > 0:
                        scaled_back = pygame.transform.scale(self.card_back, (width, self.card_height))
                        self.screen.blit(scaled_back, (x + (self.card_width - width) // 2, y))
                else:
                    width = int(self.card_width * ((progress - 0.5) * 2))
                    if width > 0:
                        scaled_front = pygame.transform.scale(card.image, (width, self.card_height))
                        self.screen.blit(scaled_front, (x + (self.card_width - width) // 2, y))
            
            pygame.display.flip()
            animation_frames += 1
            self.clock.tick(self.FPS)


    def spread_cards_animation(self, cards: List[Card], start_pos: Tuple[int, int],
                             initial_spacing: int, final_spacing: int,
                             redraw_game_screen) -> None:
        """Card spreading animation after flipping to front in temporary draw area"""
        animation_frames = 0
        while animation_frames < 15:
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            progress = animation_frames / 15
            current_spacing = initial_spacing + (final_spacing - initial_spacing) * progress
            
            for i, card in enumerate(cards):
                x = start_pos[0] + i * current_spacing
                y = start_pos[1]
                self.screen.blit(card.image, (x, y))
            
            pygame.display.flip()
            animation_frames += 1
            self.clock.tick(self.FPS)


    def display_cards_temporarily(self, cards: List[Card], position: Tuple[int, int],
                                spacing: int, redraw_game_screen) -> None:
        """Display cards drawed temporarily in temporary draw area after spreading"""
        display_time = 0
        while display_time < 60:
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            for i, card in enumerate(cards):
                x = position[0] + i * spacing
                y = position[1]
                self.screen.blit(card.image, (x, y))
            
            pygame.display.flip()
            display_time += 1
            self.clock.tick(self.FPS)


    def move_to_temp_display_area(self, cards: List[Card], start_pos: Tuple[int, int],
                             target_pos: Tuple[int, int], spacing: int,
                             redraw_game_screen) -> None:
        """Card moving from temporary draw area to temporary display area, at the leftmost side of the player's hand area"""
        MOVE_FRAMES = 10
        for frame in range(MOVE_FRAMES):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            progress = frame / MOVE_FRAMES
            for i, card in enumerate(cards):
                original_x = start_pos[0] + i * spacing
                original_y = start_pos[1]
                
                current_x = original_x + (target_pos[0] - original_x) * progress
                current_y = original_y + (target_pos[1] - original_y) * progress
                
                self.screen.blit(card.image, (int(current_x), int(current_y)))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)


    def show_in_temp_display_area(self, cards: List[Card], position: Tuple[int, int],
                         spacing: int, redraw_game_screen) -> None:
        """Show cards drawed temporarily in temporary display area, before actually adding to player's hand"""
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 1000:
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            for i, card in enumerate(cards):
                self.screen.blit(card.image, (position[0] + i * spacing, position[1]))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)

    
    def flip_player_cards_to_back(self, target_player: Player, redraw_game_screen) -> None:
        """Flip cards to back in target player's hand"""
        animation_frames = 0
        while animation_frames < 20:
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))

            target_cards = target_player.cards.copy()
            target_player.cards = []  

            redraw_game_screen()

            target_player.cards = target_cards

            progress = animation_frames / 20
            for card in target_cards:
                original_x = card.rect.x
                original_y = card.rect.y
                
                if progress < 0.5:
                    width = int(self.card_width * (1 - progress * 2))
                    if width > 0:
                        scaled_card = pygame.transform.scale(card.image, (width, self.card_height))
                        self.screen.blit(scaled_card, 
                                    (original_x + (self.card_width - width) // 2, 
                                        original_y))
                else:
                    width = int(self.card_width * ((progress - 0.5) * 2))
                    if width > 0:
                        scaled_back = pygame.transform.scale(self.card_back, (width, self.card_height))
                        self.screen.blit(scaled_back, 
                                    (original_x + (self.card_width - width) // 2, 
                                        original_y))
            
            pygame.display.flip()
            animation_frames += 1
            self.clock.tick(self.FPS)
            

    def shuffle_in_player_hand(self, target_player: Player, center_pos: Tuple[int, int], 
                        redraw_game_screen) -> None:
        """Shuffling animation for cards in player's hand"""
        center_x, center_y = center_pos
        num_cards = len(target_player.cards)
        
        for _ in range(2):  
            self._split_cards_animation(center_x, center_y, 15, num_cards, 
                                      target_player, redraw_game_screen)
            self._merge_cards_animation(center_x, center_y, 20, num_cards, 
                                      target_player, redraw_game_screen)


    def reveal_selected_card(self, card: Card, redraw_game_screen) -> None:
        """Revealing a selected card"""
        card.selected = True
        redraw_game_screen()
        pygame.display.flip()
        pygame.time.wait(500)
        
        card.face_down = False
        redraw_game_screen()
        pygame.display.flip()
        pygame.time.wait(500)

    
    def discard_card_animation(self, card: Card, start_pos: Tuple[int, int], 
                         target_pos: Tuple[int, int], redraw_game_screen) -> None:
        """Single card discard animation including rise, flight and flip"""
        # Rise animation
        RISE_FRAMES = 18
        RISE_HEIGHT = -50
        
        for frame in range(RISE_FRAMES):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            rise_progress = frame / RISE_FRAMES
            current_y = start_pos[1] + RISE_HEIGHT * rise_progress
            
            self.screen.blit(card.image, (start_pos[0], current_y))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)

        # Flight and flip animation
        FLIGHT_FRAMES = 30
        for frame in range(FLIGHT_FRAMES):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            flight_progress = frame / FLIGHT_FRAMES
            smooth_progress = (1 - (1 - flight_progress) * (1 - flight_progress))
            current_x = start_pos[0] + (target_pos[0] - start_pos[0]) * smooth_progress
            current_y = start_pos[1] + RISE_HEIGHT + (target_pos[1] - (start_pos[1] + RISE_HEIGHT)) * smooth_progress
            
            if flight_progress < 0.5:
                width = int(self.card_width * (1 - flight_progress * 2))
                if width > 0:
                    scaled_card = pygame.transform.scale(card.image, (width, self.card_height))
                    self.screen.blit(scaled_card, (current_x + (self.card_width - width) // 2, current_y))
            else:
                width = int(self.card_width * ((flight_progress - 0.5) * 2))
                if width > 0:
                    scaled_card = pygame.transform.scale(self.card_back, (width, self.card_height))
                    self.screen.blit(scaled_card, (current_x + (self.card_width - width) // 2, current_y))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)

    
    def get_two_players_positions(self):
        if not self.game:
            return
        
        computer_y = 150  
        human_y = self.game.height - 200  
        
        start_x = self.game.CARD_LEFT_MARGIN
        
        return [(start_x, computer_y), (start_x, human_y)]

    def get_three_players_positions(self):
        if not self.game:
            return
        
        computer1_y = 150  
        computer2_y = 300  
        human_y = self.game.height - 200  
    
        start_x = self.game.CARD_LEFT_MARGIN
        
        return [(start_x, computer1_y), (start_x, computer2_y), (start_x, human_y)]
    
    def deal_cards_with_trailing_effect(self, deck_positions: List[Tuple[int, int]], player_positions: List[Tuple[int, int]]):
        card_spacing = 70
        cards_per_row = 5  

        expanded_positions = []
        for base_x, base_y in player_positions:
            expanded_positions.extend([(base_x + i * card_spacing, base_y) for i in range(cards_per_row)])

        current_card = 0
        cards_at_target = []
        trail_positions = [] 

        while current_card < len(expanded_positions):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))

            deck_x, deck_y = deck_positions[0]
            remaining_cards = len(expanded_positions) - current_card
            for i in range(min(remaining_cards, 20)):
                offset = i * 2
                self.screen.blit(self.card_back, (deck_x, deck_y - offset))

            for idx in cards_at_target:
                self.screen.blit(self.card_back, expanded_positions[idx])

            for pos, alpha in trail_positions:
                card_surface = self.card_back.copy()
                card_surface.set_alpha(alpha)
                self.screen.blit(card_surface, pos)

            current_pos = deck_positions[0]
            target_pos = expanded_positions[current_card]
            step_x = (target_pos[0] - current_pos[0]) * 0.3  
            step_y = (target_pos[1] - current_pos[1]) * 0.3 
            deck_positions[0] = (current_pos[0] + step_x, current_pos[1] + step_y)

            trail_positions.append((deck_positions[0], 255))
            if len(trail_positions) > 8:
                trail_positions.pop(0)

            trail_positions = [(pos, max(alpha - 34, 0)) for pos, alpha in trail_positions] 

            x, y = deck_positions[0]
            self.screen.blit(self.card_back, (x, y))

            if abs(target_pos[0] - current_pos[0]) < 5 and abs(target_pos[1] - current_pos[1]) < 5:
                cards_at_target.append(current_card)
                current_card += 1

            pygame.display.flip()
            self.clock.tick(self.FPS * 3)

        for row_idx, (player_x, player_y) in enumerate(player_positions):
            row_start = row_idx * cards_per_row
            row_end = min(row_start + cards_per_row, len(expanded_positions))  # 防止溢出

            all_cards_collected = False
            while not all_cards_collected:
                all_cards_collected = True
                self.screen.fill(self.background_color)
                self.screen.blit(self.background, (0, 0))

                for card_idx, pos in enumerate(expanded_positions):
                    if card_idx < row_start or card_idx >= row_end:  # 非当前行
                        x, y = pos
                        self.screen.blit(self.card_back, (x, y))

                for card_idx in range(row_start, row_end):
                    current_pos = expanded_positions[card_idx]
                    target_pos = (player_x, current_pos[1])

                    if abs(target_pos[0] - current_pos[0]) > 5:
                        all_cards_collected = False  
                        step_x = (target_pos[0] - current_pos[0]) * 0.1 
                        expanded_positions[card_idx] = (
                            current_pos[0] + step_x,
                            current_pos[1], 
                        )

                    x, y = expanded_positions[card_idx]
                    self.screen.blit(self.card_back, (x, y))

                pygame.display.flip()
                self.clock.tick(self.FPS * 2)
