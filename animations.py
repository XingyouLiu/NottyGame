import pygame
from typing import Tuple, List

class CardAnimations:
    def __init__(self, screen: pygame.Surface, card_images: dict):
        self.screen = screen
        self.card_images = card_images
        self.animation_speed = 5 
        
    def draw_card_animation(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], card: Tuple[str, int]):
        """从牌堆抽牌的动画"""
        pass
        
    def flip_card_animation(self, pos: Tuple[int, int], card: Tuple[str, int]):
        """翻牌动画"""
        pass
        
    def discard_animation(self, start_positions: List[Tuple[int, int]], end_pos: Tuple[int, int], cards: List[Tuple[str, int]]):
        """弃牌动画"""
        pass
        
    def take_card_animation(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], card: Tuple[str, int]):
        """拿取其他玩家的牌的动画"""
        pass
        
    def shuffle_animation(self, deck_pos: Tuple[int, int]):
        """洗牌动画"""
        pass

class UIAnimations:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        
    def button_hover_animation(self, button_rect: pygame.Rect):
        """按钮悬停效果"""
        pass
        
    def message_fade_animation(self, message: str, pos: Tuple[int, int]):
        """消息淡入淡出效果"""
        pass 
