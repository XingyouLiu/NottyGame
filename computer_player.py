from player import Player
import random
from typing import Tuple, Optional, Dict
from collection_of_cards import CollectionOfCards
from collections import Counter
import math
import itertools

class ComputerPlayer(Player):
    def __init__(self, name: str):
        super().__init__(name, is_human=False)


class RandomStrategyPlayer(ComputerPlayer):
    """Computer player that chooses actions randomly"""
    def choose_first_action(self, game_state: Dict) -> Tuple[str, Optional[Player]]:
        """
        Returns: (action_type, target_player)
        action_type: 'draw', 'take', or 'pass'
        target_player: Player object if action is 'take', None otherwise
        """
        if len(game_state['current_player'].hand) > 19:
            return ('pass', None, None)
        
        choices = []
        if len(game_state['other_players']) == 1:
            choices = [('draw', 1, None), ('draw', 2, None), ('draw', 3, None), ('take', None, game_state['other_players'][0]), ('pass', None, None)]
        elif len(game_state['other_players']) == 2:
            choices = [('draw', 1, None), ('draw', 2, None), ('draw', 3, None), ('take', None, game_state['other_players'][0]), ('take', None, game_state['other_players'][1]), ('pass', None, None)]

        elif len(game_state['current_player'].hand) > 18:
            choices.pop(('draw', 3, None))
            choices.pop(('draw', 2, None))
        elif len(game_state['current_player'].hand) > 17:
            choices.pop(('draw', 3, None))

        return random.choice(choices)
    

    def choose_second_action(self, game_state: Dict, first_action: str) -> Tuple[str, Optional[int], Optional[Player]]:
        if len(game_state['current_player'].hand) > 19:
            return ('pass', None, None)
        
        choices = []
        if first_action == 'draw':
            if len(game_state['other_players']) == 1:
                choices = [('take', None, game_state['other_players'][0]), ('pass', None, None)]
            elif len(game_state['other_players']) == 2:
                choices = [('take', None, game_state['other_players'][0]), ('pass', None, None)]
        elif first_action == 'take':
            choices = [('draw', 1, None), ('draw', 2, None), ('draw', 3, None), ('pass', None, None)]
            if len(game_state['current_player'].hand) > 18:
                choices.pop(('draw', 3, None))
                choices.pop(('draw', 2, None))
            elif len(game_state['current_player'].hand) > 17:
                choices.pop(('draw', 3, None))
        
        return random.choice(choices)
        
        
    def get_strategy_name(self) -> str:
        return "Random Strategy"
    

class ExpectationValueStrategyPlayer(ComputerPlayer):
    """Computer player that calculates expectations before choosing actions"""
    def __init__(self, name: str):
        super().__init__(name)
        self.continuous_pass_count = 0

    
    def choose_first_action(self, game_state: Dict) -> Tuple[str, Optional[int], Optional[Player]]:
        """
        Returns: (action_type, draw_count, target_player)
        action_type: 'draw', 'take', or 'pass'
        draw_count: number of cards to draw if action is 'draw', None otherwise
        target_player: Player object if action is 'take', None otherwise
        """
        if len(game_state['current_player'].hand) > 19:
            return ('pass', None, None)
        
        expectations = self.calculate_expectation(game_state)

        if len(game_state['current_player'].hand) > 18:
            expectations.pop(('draw', 2, None))
            expectations.pop(('draw', 3, None))
        elif len(game_state['current_player'].hand) > 17:
            expectations.pop(('draw', 3, None))
            
        print(f"choose first action: {expectations}")

        best_action = max(expectations, key=lambda x: expectations[x])
        action_type = best_action[0]

        if action_type == 'pass':
            self.continuous_pass_count += 1
        else:
            self.continuous_pass_count = 0

        if self.continuous_pass_count > 1:
            expectations.pop(('pass', None, None))
            best_action = max(expectations, key=lambda x: expectations[x])
            action_type = best_action[0]
            self.continuous_pass_count = 0
        
        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.hand) <= 2:
                expectations.pop(('take', None, target_player))
                best_action = max(expectations, key=lambda x: expectations[x])
                action_type = best_action[0]
            else:
                return action_type, None, target_player

        if action_type == 'draw':
            draw_count = best_action[1]
            return action_type, draw_count, None
        
        if action_type == 'pass':
            return action_type, None, None
        
        
    def choose_second_action(self, game_state: Dict, first_action: str) -> Tuple[str, Optional[int], Optional[Player]]:
        if len(game_state['current_player'].hand) > 19:
            return ('pass', None, None)
        
        expectations = self.calculate_expectation(game_state)

        if first_action == 'draw':
            expectations = {k: v for k, v in expectations.items() if k[0] != 'draw'}
        elif first_action == 'take':
            expectations = {k: v for k, v in expectations.items() if k[0] != 'take'}

            if len(game_state['current_player'].hand) > 18:
                expectations.pop(('draw', 2, None))
                expectations.pop(('draw', 3, None))
            elif len(game_state['current_player'].hand) > 17:
                expectations.pop(('draw', 3, None))

        print(f"choose second action: {expectations}")
        
        best_action = max(expectations, key=lambda x: expectations[x])
        action_type = best_action[0]

        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.hand) <= 2:
                expectations.pop(('take', None, target_player))
                best_action = max(expectations, key=lambda x: expectations[x])
                action_type = best_action[0]
            else:
                return action_type, None, target_player

        if action_type == 'draw':
            draw_count = best_action[1]
            return action_type, draw_count, None
        
        if action_type == 'pass':
            return action_type, None, None
    
    
    def calculate_expectation(self, game_state: Dict) -> Dict[Tuple[str, Optional[int], Optional[Player]], float]:
        """
        Returns: Dictionary: key: action types, value: (expected_value, draw_count, target_player) tuples
        draw_count is None for 'take' and 'pass' actions
        target_player is None for 'draw' and 'pass' actions
        """
        collection = CollectionOfCards(game_state['current_player'].hand)
        expected_values = {}
        
        for draw_count in range(1, 4):
            draw_expected_value = 0
            if draw_count == 1:
                deck_counter = Counter(game_state['deck_cards'])
                for card, count in deck_counter.items():
                    collection.collection.append(card)
                    if collection.exist_valid_group():
                        draw_expected_value += count * 1 / game_state['deck_size'] * len(collection.largest_valid_group())
                    collection.collection.pop()
                expected_values[('draw', 1, None)] = draw_expected_value - draw_count

            else:
                combination_count = math.factorial(game_state['deck_size']) // (math.factorial(draw_count) * math.factorial(game_state['deck_size'] - draw_count))
                for combination in itertools.combinations(game_state['deck_cards'], draw_count):
                    for card in combination:
                        collection.collection.append(card)
                    if collection.exist_valid_group():
                        draw_expected_value += len(collection.largest_valid_group()) * 1 / combination_count
                    for card in combination:
                        collection.collection.pop()
                expected_values[('draw', draw_count, None)] = draw_expected_value - draw_count

        for player in game_state['other_players']:
            take_expected_value = 0
            player_counter = Counter(player.hand)
            for card, count in player_counter.items():
                collection.collection.append(card)
                if collection.exist_valid_group():
                    take_expected_value += count * 1 / len(player.hand) * len(collection.largest_valid_group())
                collection.collection.pop()
            expected_values[('take', None, player)] = take_expected_value - 1

        expected_values[('pass', None, None)] = 0

        return expected_values

        
    def get_strategy_name(self) -> str:
        return "Calculating Strategy"
    

class ProbabilityStrategyPlayer(ComputerPlayer):
    """Computer player that calculates probabilities of getting valid groups before choosing actions"""
    def choose_first_action(self, game_state: Dict) -> Tuple[str, Optional[int], Optional[Player]]:
        """
        Returns: (action_type, draw_count, target_player)
        action_type: 'draw', 'take', or 'pass'
        draw_count: number of cards to draw if action is 'draw', None otherwise
        target_player: Player object if action is 'take', None otherwise
        """
        if len(game_state['current_player'].hand) > 19:
            return ('pass', None, None)
        
        probabilities = self.calculate_probability(game_state)

        if len(game_state['current_player'].hand) > 18:
            probabilities.pop(('draw', 2, None))
            probabilities.pop(('draw', 3, None))
        elif len(game_state['current_player'].hand) > 17:
            probabilities.pop(('draw', 3, None))

        print(f"choose first action: {probabilities}")

        best_action = max(probabilities, key=lambda x: probabilities[x])
        action_type = best_action[0]

        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.hand) <= 2:
                probabilities.pop(('take', None, target_player))
                best_action = max(probabilities, key=lambda x: probabilities[x])
                action_type = best_action[0]
            else:
                return action_type, None, target_player
            
        if action_type == 'draw':
            draw_count = best_action[1]
            return action_type, draw_count, None
        
        if action_type == 'pass':
            return action_type, None, None
        

    def choose_second_action(self, game_state: Dict, first_action: str) -> Tuple[str, Optional[int], Optional[Player]]:
        if len(game_state['current_player'].hand) > 19:
            return ('pass', None, None)
        
        probabilities = self.calculate_probability(game_state)

        if first_action == 'draw':
            probabilities = {k: v for k, v in probabilities.items() if k[0] != 'draw'}
        elif first_action == 'take':
            probabilities = {k: v for k, v in probabilities.items() if k[0] != 'take'}

            if len(game_state['current_player'].hand) > 18:
                probabilities.pop(('draw', 2, None))
                probabilities.pop(('draw', 3, None))
            elif len(game_state['current_player'].hand) > 17:
                probabilities.pop(('draw', 3, None))

        print(f"choose second action: {probabilities}")
        
        best_action = max(probabilities, key=lambda x: probabilities[x])
        action_type = best_action[0]

        if probabilities[best_action] == 0:
            action_type = 'pass'

        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.hand) <= 2:
                probabilities.pop(('take', None, target_player))
                best_action = max(probabilities, key=lambda x: probabilities[x])
                action_type = best_action[0]
            else:
                return action_type, None, target_player
            
        if action_type == 'draw':
            draw_count = best_action[1]
            return action_type, draw_count, None
        
        if action_type == 'pass':
            return action_type, None, None
        

    def calculate_probability(self, game_state: Dict) -> Dict[Tuple[str, Optional[int], Optional[Player]], float]:
        collection = CollectionOfCards(game_state['current_player'].hand)
        probabilities = {}
        
        for draw_count in range(1, 4):
            valid_count = 0
            if draw_count == 1:
                deck_counter = Counter(game_state['deck_cards'])
                for card, count in deck_counter.items():
                    collection.collection.append(card)
                    if collection.exist_valid_group():
                        valid_count += count
                    collection.collection.pop()
                probabilities[('draw', 1, None)] = valid_count / game_state['deck_size']

            else:
                combination_count = math.factorial(game_state['deck_size']) // (math.factorial(draw_count) * math.factorial(game_state['deck_size'] - draw_count))
                for combination in itertools.combinations(game_state['deck_cards'], draw_count):
                    for card in combination:
                        collection.collection.append(card)
                    if collection.exist_valid_group():
                        valid_count += 1
                    for card in combination:
                        collection.collection.pop()
                probabilities[('draw', draw_count, None)] = valid_count / combination_count

        for player in game_state['other_players']:
            valid_count = 0
            player_counter = Counter(player.hand)
            for card, count in player_counter.items():
                collection.collection.append(card)
                if collection.exist_valid_group():
                    valid_count += count
                collection.collection.pop()
            probabilities[('take', None, player)] = valid_count / len(player.hand)

        probabilities[('pass', None, None)] = 0

        return probabilities
    
    def get_strategy_name(self) -> str:
        return "Probability Strategy"

