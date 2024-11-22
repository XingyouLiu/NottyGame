from typing import List, Tuple, Optional
from collection_of_cards import CollectionOfCards
from card import Card

class Player:
    def __init__(self, name: str, is_human: bool = True):
        self.name = name
        self.is_human = is_human
        self.cards: List[Card] = []  
        self.hand: List[Tuple[str, int]] = []  

    def add_card(self, card_tuple: Tuple[str, int], position: Tuple[int, int] = (0, 0)):
        new_card = Card(card_tuple[0], card_tuple[1], position)
        self.cards.append(new_card)
        self.hand.append(card_tuple)

    def remove_card(self, card: Card) -> Card:
        card_index = self.cards.index(card)
        self.hand.pop(card_index)
        removed_card = self.cards.pop(card_index)
        return removed_card

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

    def clear_selections(self):
        for card in self.cards:
            card.selected = False
            card.hover = False
            card.invalid = False
