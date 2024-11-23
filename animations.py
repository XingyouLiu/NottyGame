import pygame
from card import Card
import random
from typing import List, Tuple

class CardAnimation:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, 
                 card_back: pygame.Surface, background: pygame.Surface,
                 background_color: Tuple[int, int, int],
                 card_width: int, card_height: int):
        self.screen = screen
        self.clock = clock
        self.card_back = card_back
        self.background = background
        self.background_color = background_color
        self.FPS = 60
        self.card_width = card_width
        self.card_height = card_height

    def shuffle_animation(self, deck_area: pygame.Rect, card_width: int, card_height: int, 
                         redraw_game_screen=None):
        """Deck shuffling animation"""
        ANIMATION_FRAMES = 30
        CARDS_PER_ANIMATION = 5
        SHUFFLE_ROUNDS = 2
        
        deck_x = deck_area.x
        deck_y = deck_area.y
        
        for _ in range(SHUFFLE_ROUNDS):
            self._split_deck_animation(deck_x, deck_y, ANIMATION_FRAMES, redraw_game_screen)
            self._merge_deck_animation(deck_x, deck_y, ANIMATION_FRAMES, redraw_game_screen)


    def _split_deck_animation(self, deck_x: int, deck_y: int, frames: int, redraw_game_screen=None):
        """Deck splitting during shuffling"""
        for frame in range(frames):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            
            if redraw_game_screen:
                redraw_game_screen()
            
            progress = frame / frames
            offset = int(50 * progress)
            
            for i in range(10):
                x = deck_x - offset + i * 2
                y = deck_y + i * 2
                self.screen.blit(self.card_back, (x, y))
            
            for i in range(10):
                x = deck_x + offset + i * 2
                y = deck_y + i * 2
                self.screen.blit(self.card_back, (x, y))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)

    def _merge_deck_animation(self, deck_x: int, deck_y: int, frames: int, redraw_game_screen=None):
        """Deck merging during shuffling"""
        for frame in range(frames):
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            
            if redraw_game_screen:
                redraw_game_screen()
            
            progress = frame / frames
            offset = int(50 * (1 - progress))
            
            for i in range(10):
                x = deck_x - offset + int(offset * 2 * progress) + i * 2
                y = deck_y + i * 2 + int(10 * (1 - progress))
                self.screen.blit(self.card_back, (x, y))
                
                x = deck_x + offset - int(offset * 2 * progress) + i * 2
                y = deck_y + i * 2 - int(10 * (1 - progress))
                self.screen.blit(self.card_back, (x, y))
            
            pygame.display.flip()
            self.clock.tick(self.FPS)
            

    def draw_to_temp_draw_area(self, start_pos: Tuple[int, int], target_pos: Tuple[int, int], 
                         redraw_game_screen) -> None:
        """Card moving from deck to temporary draw area"""
        animation_frames = 0
        max_frames = 30
        
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
            self.clock.tick(60)

    def flip_cards_animation(self, cards: List[Card], positions: List[Tuple[int, int]], 
                           redraw_game_screen) -> None:
        """Card flipping animation in temporary draw area"""
        animation_frames = 0
        while animation_frames < 20:
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
        while animation_frames < 30:
            self.screen.fill(self.background_color)
            self.screen.blit(self.background, (0, 0))
            redraw_game_screen()
            
            progress = animation_frames / 30
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
        while display_time < 120:
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
        MOVE_FRAMES = 20
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

    


class UIAnimations:
    def __init__(self, screen: pygame.Surface):
        pass
        
    def button_hover_animation(self, button_rect: pygame.Rect):
        """按钮悬停效果"""
        pass
        
    def message_fade_animation(self, message: str, pos: Tuple[int, int]):
        """消息淡入淡出效果"""
        pass 
