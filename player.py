from typing import List, Tuple, Optional, Dict
from collection_of_cards import CollectionOfCards
from card import Card
import math
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor

class Player:
    def __init__(self, name: str, is_human: bool = True):
        self.name = name
        self.is_human = is_human
        self.cards: List[Card] = []    

    def add_card(self, card: Card, position: Tuple[int, int] = (0, 0), animate: bool = False):
        card.set_position(position[0], position[1], animate=animate)
        self.cards.append(card)

    def remove_card(self, card: Card) -> Card:
        card_index = self.cards.index(card)
        removed_card = self.cards.pop(card_index)
        return removed_card

    def exist_valid_group(self) -> bool:
        collection = CollectionOfCards(self.cards)
        return collection.exist_valid_group()
    
    
    def is_valid_group(self, cards: List[Card]) -> bool:
        collection = CollectionOfCards(cards)
        return collection.is_valid_group()
    
    
    def largest_valid_group(self) -> List[Card]:
        collection = CollectionOfCards(self.cards)
        return collection.largest_valid_group()
    
    
    def all_valid_groups_with_largest_length(self) -> List[List[Card]]:
        collection = CollectionOfCards(self.cards)
        return collection.all_valid_groups_with_largest_length()
    
    def all_valid_groups(self) -> List[List[Card]]:
        collection = CollectionOfCards(self.cards)
        return collection.all_valid_groups()
    

    def find_best_discard(self):
        collection = CollectionOfCards(self.cards)
        return collection.find_best_discard()
    
    def calculate_probability(self, game_state: Dict):
        collection = CollectionOfCards(game_state['current_player'].cards.copy())
        probabilities = {}
        
        for draw_count in range(1, 4):
            valid_count = 0
            if draw_count == 1:
                for card in game_state['deck_cards']:
                    collection.collection.append(card)
                    if collection.exist_valid_group():
                        valid_count += 1
                    collection.collection.pop()
                probabilities[('draw', 1, None)] = valid_count / game_state['deck_size']

            else:
                combination_count = math.factorial(game_state['deck_size']) // (math.factorial(draw_count) * math.factorial(game_state['deck_size'] - draw_count))
                for combination in combinations(game_state['deck_cards'], draw_count):
                    for card in combination:
                        collection.collection.append(card)
                    if collection.exist_valid_group():
                        valid_count += 1
                    for card in combination:
                        collection.collection.pop()
                probabilities[('draw', draw_count, None)] = valid_count / combination_count

        for player in game_state['other_players']:
            valid_count = 0
            for card in player.cards:
                collection.collection.append(card)
                if collection.exist_valid_group():
                    valid_count += 1
                collection.collection.pop()
            probabilities[('take', None, player)] = valid_count / len(player.cards)

        probabilities[('pass', None, None)] = 0

        return probabilities
    

    def calculate_draw_expectation(self, draw_count: int, game_state: Dict) -> Tuple[Tuple, float]:
        collection = CollectionOfCards(game_state['current_player'].cards.copy())
        draw_expected_value = 0
        
        if draw_count == 1:
            for card in game_state['deck_cards']:
                collection.collection.append(card)
                if collection.exist_valid_group():
                    draw_expected_value += collection.find_best_discard()[1] * 1 / game_state['deck_size']
                collection.collection.pop()
            return (('draw', 1, None), draw_expected_value - draw_count)
        else:
            combination_count = math.factorial(game_state['deck_size']) // (
                math.factorial(draw_count) * math.factorial(game_state['deck_size'] - draw_count))
            for combination in combinations(game_state['deck_cards'], draw_count):
                for card in combination:
                    collection.collection.append(card)
                if collection.exist_valid_group():
                    draw_expected_value += collection.find_best_discard()[1] * 1 / combination_count
                for card in combination:
                    collection.collection.pop()
            return (('draw', draw_count, None), draw_expected_value - draw_count)
        
    def calculate_take_expectations(self, game_state: Dict) -> List[Tuple[Tuple, float]]:
        collection = CollectionOfCards(game_state['current_player'].cards.copy())
        results = []
        for player in game_state['other_players']:
            take_expected_value = 0
            for card in player.cards:
                collection.collection.append(card)
                if collection.exist_valid_group():
                    take_expected_value += collection.find_best_discard()[1] * 1 / len(player.cards)
                collection.collection.pop()
            results.append((('take', None, player), take_expected_value - 1))
        return results
    

    def draw_expectation(self, game_state: Dict):
        """
        Returns: Dictionary: key: action types, value: (expected_value, draw_count, target_player) tuples
        draw_count is None for 'take' and 'pass' actions
        target_player is None for 'draw' and 'pass' actions
        """
        draw_expected_values = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            draw_futures = [
                executor.submit(self.calculate_draw_expectation, i, game_state)
                for i in range(1, 4)
            ]
            
            for future in draw_futures:
                action, value = future.result()
                draw_expected_values[action] = value
        
        return draw_expected_values
    

    def take_expectation(self, game_state: Dict):
        """
        Returns: Dictionary: key: action types, value: (expected_value, draw_count, target_player) tuples
        draw_count is None for 'take' and 'pass' actions
        target_player is None for 'draw' and 'pass' actions
        """
        take_expected_values = {}
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            take_future = executor.submit(
                self.calculate_take_expectations, 
                game_state
            )

            for action, value in take_future.result():
                take_expected_values[action] = value
                
        return take_expected_values


    def clear_selections(self):
        for card in self.cards:
            card.selected = False
            card.hover = False
            card.invalid = False
