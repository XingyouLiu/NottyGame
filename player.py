from typing import List, Tuple
from collection_of_cards import CollectionOfCards
import random

class Player:
    def __init__(self, name: str, is_human: bool = True) -> None:
        self.name = name
        self.hand: List[Tuple[str, int]] = []
        self.is_human = is_human


    def add_card(self, card: Tuple[str, int]) -> None:
        self.hand.append(card)


    def remove_card(self, card: Tuple[str, int]) -> None:
        self.hand.remove(card)


    def show_cards(self) -> str:
        return ', '.join(card[0] + ' ' + str(card[1]) for card in self.hand)
    

    def exist_valid_group(self) -> bool:
        collection = CollectionOfCards(self.hand)
        return collection.exist_valid_group()
    
    
    def is_valid_group(self, cards: List[Tuple[str, int]]) -> bool:
        collection = CollectionOfCards(cards)
        return collection.is_valid_group()
    
    
    def largest_valid_group(self) -> List[Tuple[str, int]]:
        collection = CollectionOfCards(self.hand)
        return collection.largest_valid_group()
    
    
    def all_valid_groups_with_largest_length(self) -> List[List[Tuple[str, int]]]:
        collection = CollectionOfCards(self.hand)
        return collection.all_valid_groups_with_largest_length()
    
    
    def probability_exist_valid_group_drawing_one_card(self) -> float:
        collection = CollectionOfCards(self.hand)
        return collection.probability_exist_valid_group_drawing_one_card()
    
    def get_computer_action(self, available_actions: List[str]) -> str:
        return random.choice(available_actions)

    def should_continue_drawing(self) -> bool:
        return random.choice([True, False])
