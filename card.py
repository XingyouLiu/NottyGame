import pygame
from typing import Tuple

class Card:
    # 类变量，所有实例共享
    back_image = None
    
    @classmethod
    def initialize_back_image(cls, card_width: int, card_height: int):
        """初始化卡片背面图片（只需要执行一次）"""
        if cls.back_image is None:
            cls.back_image = pygame.image.load('cards/card_back.jpg')
            cls.back_image = pygame.transform.scale(cls.back_image, (card_width, card_height))

    def __init__(self, color: str, number: int, 
                 card_width: int = 60, card_height: int = 100,
                 position: Tuple[int, int] = (0, 0)):
        
        self.color = color
        self.number = number
        self.card_width = card_width
        self.card_height = card_height
        
        # Load card image
        self.image = pygame.image.load(f'cards/{color}_{number}.png')
        self.image = pygame.transform.scale(self.image, (card_width, card_height))
        self.original_image = self.image.copy()
        
        # Ensure back image is initialized
        Card.initialize_back_image(card_width, card_height)
        
        # Create rectangle for collision detection and positioning
        self.rect = self.image.get_rect()
        self.rect.topleft = position
        
        # States
        self.selected = False
        self.hover = False
        self.invalid = False
        
        # Animation properties
        self.target_x = position[0]
        self.current_x = position[0]
        self.animation_speed = 16
        
        # 添加一个新的状态属性
        self.face_down = False
        

        
    def update(self):
        # Handle card animation
        if self.current_x != self.target_x:
            dx = (self.target_x - self.current_x) / self.animation_speed
            self.current_x += dx
            self.rect.x = int(self.current_x)
        
        # 修改图像显示逻辑
        if self.face_down:
            self.image = Card.back_image.copy()
        else:
            self.image = self.original_image.copy()
            
        # Add visual effects based on current state
        if self.invalid:
            pygame.draw.rect(self.image, (255, 0, 0), (0, 0, self.card_width, self.card_height), 3)
        elif self.selected:
            pygame.draw.rect(self.image, (0, 255, 0), (0, 0, self.card_width, self.card_height), 3)
        elif self.hover:
            pygame.draw.rect(self.image, (255, 255, 0), (0, 0, self.card_width, self.card_height), 2)
    
    def set_position(self, x: int, y: int, animate: bool = False):
        if animate:
            self.target_x = x
        else:
            self.current_x = x
            self.target_x = x
            self.rect.x = x
        self.rect.y = y
        
    def contains_point(self, point: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(point)

    def reset_state(self):
        """完全重置卡片到原始状态"""
        self.selected = False
        self.hover = False
        self.invalid = False
        self.image = self.original_image.copy()
