import pygame
from card import Card
import random
from typing import List, Tuple

class CardAnimation:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, 
                 card_back: pygame.Surface, background: pygame.Surface,
                 background_color: Tuple[int, int, int]):
        self.screen = screen
        self.clock = clock
        self.card_back = card_back
        self.background = background
        self.background_color = background_color
        self.FPS = 60

    def shuffle_animation(self, deck_area: pygame.Rect, card_width: int, card_height: int, 
                         redraw_game_screen=None):
        ANIMATION_FRAMES = 30
        CARDS_PER_ANIMATION = 5
        SHUFFLE_ROUNDS = 2
        
        deck_x = deck_area.x
        deck_y = deck_area.y
        
        for _ in range(SHUFFLE_ROUNDS):
            self._split_deck_animation(deck_x, deck_y, ANIMATION_FRAMES, redraw_game_screen)
            self._merge_deck_animation(deck_x, deck_y, ANIMATION_FRAMES, redraw_game_screen)


    def _split_deck_animation(self, deck_x: int, deck_y: int, frames: int, redraw_game_screen=None):
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


class UIAnimations:
    def __init__(self, screen: pygame.Surface):
        pass
        
    def button_hover_animation(self, button_rect: pygame.Rect):
        """按钮悬停效果"""
        pass
        
    def message_fade_animation(self, message: str, pos: Tuple[int, int]):
        """消息淡入淡出效果"""
        pass 
