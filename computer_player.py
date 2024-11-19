from player import Player
import random
from typing import Tuple, Optional, Dict
from collection_of_cards import CollectionOfCards
from collections import Counter

class ComputerPlayer(Player):
    def __init__(self, name: str):
        super().__init__(name, is_human=False)


class RandomStrategyPlayer(ComputerPlayer):
    """Computer player that chooses actions randomly"""
    def choose_action(self, game_state: Dict) -> Tuple[str, Optional[Player]]:
        """
        Returns: (action_type, target_player)
        action_type: 'draw', 'take', or 'pass'
        target_player: Player object if action is 'take', None otherwise
        """
        choices = ['draw', 'take', 'pass']
        action = random.choice(choices)
        
        if action == 'take' and game_state['other_players']:
            target_player = random.choice(game_state['other_players'])
            return action, target_player
        
        return action, None
    
    def continue_draw(self, game_state: Dict) -> bool:
        return random.choice([0, 1]) == 0
        
    def get_strategy_name(self) -> str:
        return "Random Strategy"
    

class ExpectationValueStrategyPlayer(ComputerPlayer):
    """Computer player that calculates expectations before choosing actions"""
    def __init__(self, name: str):
        super().__init__(name)
        self.continuous_pass_count = 0

    
    def choose_action(self, game_state: Dict) -> Tuple[str, Optional[Player]]:
        """
        Returns: (action_type, target_player)
        action_type: 'draw', 'take', or 'pass'
        target_player: Player object if action is 'take', None otherwise
        """
        expectations = self.calculate_expectation(game_state)
        
        best_action = max(expectations.items(), key=lambda x: x[1][0])
        action_type = best_action[0]

        if action_type == 'pass':
            self.continuous_pass_count += 1
        else:
            self.continuous_pass_count = 0

        if self.continuous_pass_count > 1:
            expectations.pop('pass')
            best_action = max(expectations.items(), key=lambda x: x[1][0])
            action_type = best_action[0]
            self.continuous_pass_count = 0
        
        if action_type == 'take':
            target_player = best_action[1][1] 
            return action_type, target_player
        
        return action_type, None
    
    
    def continue_draw(self, game_state: Dict) -> bool:
        collection = CollectionOfCards(game_state['current_player'].hand)
        draw_expected_value = 0

        deck_counter = Counter(game_state['deck_cards'])
        for card, count in deck_counter.items():
            collection.collection.append(card)
            if collection.exist_valid_group():
                draw_expected_value += count * 1 / game_state['deck_size'] * len(collection.largest_valid_group())
            collection.collection.pop()

        return 1 if draw_expected_value >= 1 else 0

    
    def calculate_expectation(self, game_state: Dict) -> Dict[str, Tuple[float, Optional[Player]]]:
        """
        Returns: Dictionary: key: action types, value: (expected_value, target_player) tuples
        target_player is None for 'draw' and 'pass' actions
        """
        collection = CollectionOfCards(game_state['current_player'].hand)
        print(collection.collection)
        expected_values = {}

        draw_expected_value = 0
        deck_counter = Counter(game_state['deck_cards'])
        for card, count in deck_counter.items():
            collection.collection.append(card)
            if collection.exist_valid_group():
                draw_expected_value += count * 1 / game_state['deck_size'] * len(collection.largest_valid_group())
            collection.collection.pop()
        expected_values['draw'] = (draw_expected_value - 1, None)

        for player in game_state['other_players']:
            take_expected_value = 0
            player_counter = Counter(player.hand)
            for card, count in player_counter.items():
                collection.collection.append(card)
                if collection.exist_valid_group():
                    take_expected_value += count * 1 / len(player.hand) * len(collection.largest_valid_group())
                collection.collection.pop()
            expected_values['take'] = (take_expected_value - 1, player)

        expected_values['pass'] = (0, None)

        return expected_values

        
    def get_strategy_name(self) -> str:
        return "Calculating Strategy"
