from player import Player
import random
from typing import Tuple, Optional, Dict, List
from collection_of_cards import CollectionOfCards
from collections import Counter
import math
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

class ComputerPlayer(Player):
    def __init__(self, name: str):
        super().__init__(name, is_human=False)
        self.MAX_HAND_SIZE = 20


class RandomStrategyPlayer(ComputerPlayer):
    """Computer player that chooses actions randomly"""
    def choose_first_action(self, game_state: Dict) -> Tuple[str, Optional[int], Optional[Player]]:
        """
        Returns: (action_type, draw_count, target_player)
        action_type: 'draw', 'take', or 'pass'
        draw_count: number of cards to draw if action is 'draw', None otherwise
        target_player: Player object if action is 'take', None otherwise
        """
        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 1:
            return ('pass', None, None)
        
        choices = []
        if len(game_state['other_players']) == 1:
            choices = [('draw', 1, None), ('draw', 2, None), ('draw', 3, None), ('take', None, game_state['other_players'][0]), ('pass', None, None)]
        elif len(game_state['other_players']) == 2:
            choices = [('draw', 1, None), ('draw', 2, None), ('draw', 3, None), ('take', None, game_state['other_players'][0]), ('take', None, game_state['other_players'][1]), ('pass', None, None)]

        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 2:
            choices.remove(('draw', 3, None))
            choices.remove(('draw', 2, None))
        elif len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 3:
            choices.remove(('draw', 3, None))

        for player in game_state['other_players']:
            if len(player.cards) <= 2:
                choices.remove(('take', None, player))

        return random.choice(choices)
    

    def choose_second_action(self, game_state: Dict, first_action: str) -> Tuple[str, Optional[int], Optional[Player]]:
        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 1:
            return ('pass', None, None)
        
        choices = []
        if first_action == 'draw':
            if len(game_state['other_players']) == 1:
                choices = [('take', None, game_state['other_players'][0]), ('pass', None, None)]
            elif len(game_state['other_players']) == 2:
                choices = [('take', None, game_state['other_players'][0]), ('take', None, game_state['other_players'][1]), ('pass', None, None)]

            for player in game_state['other_players']:
                if len(player.cards) <= 2:
                    choices.remove(('take', None, player))
        
        elif first_action == 'take':
            choices = [('draw', 1, None), ('draw', 2, None), ('draw', 3, None), ('pass', None, None)]
            if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 2:
                choices.remove(('draw', 3, None))
                choices.remove(('draw', 2, None))
            elif len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 3:
                choices.remove(('draw', 3, None))
        
        return random.choice(choices)
        
        
    def get_strategy_name(self) -> str:
        return "DEFENSIVE"
    

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
        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 1:
            return ('pass', None, None)
        
        expectations = self.calculate_expectation(game_state)

        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 2:
            expectations.pop(('draw', 2, None))
            expectations.pop(('draw', 3, None))
        elif len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 3:
            expectations.pop(('draw', 3, None))

        best_action = max(expectations, key=lambda x: expectations[x])
        action_type = best_action[0]

        if action_type == 'pass':
            self.continuous_pass_count += 1
        else:
            self.continuous_pass_count = 0

        if self.continuous_pass_count > 2:
            expectations.pop(('pass', None, None))
            best_action = max(expectations, key=lambda x: expectations[x])
            action_type = best_action[0]
            self.continuous_pass_count = 0
        
        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.cards) <= 2:
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
        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 1:
            return ('pass', None, None)
        
        expectations = self.calculate_expectation(game_state)

        if first_action == 'draw':
            expectations = {k: v for k, v in expectations.items() if k[0] != 'draw'}
        elif first_action == 'take':
            expectations = {k: v for k, v in expectations.items() if k[0] != 'take'}

            if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 2:
                expectations.pop(('draw', 2, None))
                expectations.pop(('draw', 3, None))
            elif len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 3:
                expectations.pop(('draw', 3, None))
        
        best_action = max(expectations, key=lambda x: expectations[x])
        action_type = best_action[0]

        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.cards) <= 2:
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
        
    def calculate_draw_expectation(self, draw_count: int, game_state: Dict) -> Tuple[Tuple, float]:
        draw_expected_value = 0

        collection = CollectionOfCards(game_state['current_player'].cards.copy())
        
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
        results = []
        for player in game_state['other_players']:
            take_expected_value = 0
            collection = CollectionOfCards(game_state['current_player'].cards.copy())
            for card in player.cards:
                collection.collection.append(card)
                if collection.exist_valid_group():
                    take_expected_value += collection.find_best_discard()[1] * 1 / len(player.cards)
                collection.collection.pop()
            results.append((('take', None, player), take_expected_value - 1))
        return results
    
    
    def calculate_expectation(self, game_state: Dict) -> Dict[Tuple[str, Optional[int], Optional[Player]], float]:
        """
        Returns: Dictionary: key: action types, value: (expected_value, draw_count, target_player) tuples
        draw_count is None for 'take' and 'pass' actions
        target_player is None for 'draw' and 'pass' actions
        """
        expected_values = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            draw_futures = [
                executor.submit(self.calculate_draw_expectation, i, game_state)
                for i in range(1, 4)
            ]
            
            take_future = executor.submit(
                self.calculate_take_expectations, 
                game_state, 
            )

            for future in draw_futures:
                action, value = future.result()
                expected_values[action] = value

            for action, value in take_future.result():
                expected_values[action] = value

        expected_values[('pass', None, None)] = 0

        print(game_state['current_player'].name, "\n", expected_values)
        
        return expected_values

        
    def get_strategy_name(self) -> str:
        return "X-DEFENSIVE"
    

class ProbabilityStrategyPlayer(ComputerPlayer):
    """Computer player that calculates probabilities of getting valid groups before choosing actions"""
    def choose_first_action(self, game_state: Dict) -> Tuple[str, Optional[int], Optional[Player]]:
        """
        Returns: (action_type, draw_count, target_player)
        action_type: 'draw', 'take', or 'pass'
        draw_count: number of cards to draw if action is 'draw', None otherwise
        target_player: Player object if action is 'take', None otherwise
        """
        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 1:
            return ('pass', None, None)
        
        probabilities = self.calculate_probability(game_state)

        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 2:
            probabilities.pop(('draw', 2, None))
            probabilities.pop(('draw', 3, None))
        elif len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 3:
            probabilities.pop(('draw', 3, None))

        best_action = max(probabilities, key=lambda x: probabilities[x])
        action_type = best_action[0]

        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.cards) <= 2:
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
        if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 1:
            return ('pass', None, None)
        
        probabilities = self.calculate_probability(game_state)

        if first_action == 'draw':
            probabilities = {k: v for k, v in probabilities.items() if k[0] != 'draw'}
        elif first_action == 'take':
            probabilities = {k: v for k, v in probabilities.items() if k[0] != 'take'}

            if len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 2:
                probabilities.pop(('draw', 2, None))
                probabilities.pop(('draw', 3, None))
            elif len(game_state['current_player'].cards) >= self.MAX_HAND_SIZE - 3:
                probabilities.pop(('draw', 3, None))
        
        best_action = max(probabilities, key=lambda x: probabilities[x])
        action_type = best_action[0]

        if probabilities[best_action] == 0:
            action_type = 'pass'

        while action_type == 'take':
            target_player = best_action[2] 
            if len(target_player.cards) <= 2:
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
        collection = CollectionOfCards(game_state['current_player'].cards)
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
    
    def get_strategy_name(self) -> str:
        return "X-AGGRESSIVE"


class RulebasedStrategyPlayer(ComputerPlayer):
    """Computer player that chooses actions based on rules"""

    def choose_first_action(self, game_state: Dict) -> Tuple[str, Optional[Player]]:
        """
        Returns: (action_type, target_player)
        action_type: 'draw', 'take', or 'pass'
        target_player: Player object if action is 'take', None otherwise
        """
        # Check if it is worthy to take cards from other players, if so, take, if not, draw.
        # When opponents' hands are more than yours, and
        # opponents have one or more particular cards which could make larger valid group in you hands.
        my_hand = CollectionOfCards(game_state['current_player'].cards)
        hand_count = len(my_hand.collection)
        my_largest_group = my_hand.largest_valid_group()
        worthy_target = []

        for player in game_state['other_players']:
            # player_count = len(player.hand)
            player_hand = CollectionOfCards(player.cards)
            worthy_or_not = False
            for card in player_hand.collection:
                my_hand.collection.append(card)
                new_largest_group = my_hand.largest_valid_group()
                if my_largest_group != None and new_largest_group != None:
                    if len(new_largest_group) > len(my_largest_group):
                        worthy_or_not = True
                elif my_largest_group == None and new_largest_group != None:
                    worthy_or_not = True
                my_hand.collection.pop()
            if worthy_or_not == True:
                worthy_target.append(player)

        if worthy_target != []:
            if len(worthy_target) == 2:
                player_a = game_state['other_players'][0]
                player_b = game_state['other_players'][1]
                player_a_count = len(player_a.cards)
                player_b_count = len(player_b.cards)
                target_player = None
                if player_a_count > player_b_count and player_a_count > hand_count:
                    target_player = player_a

                if player_a_count < player_b_count and player_b_count > hand_count:
                    target_player = player_b

                if player_a_count == player_b_count and player_b_count > hand_count:
                    target_player = random.choice(worthy_target)

                if target_player is not None:
                    return ('take', None, target_player )
            else:
                other_player = worthy_target[0]
                other_player_count = len(other_player.cards)
                if other_player_count > hand_count :
                    action = 'take'
                    return (action, None, other_player)

        if hand_count < 8:
            action = 'draw'
            return (action, 3, None)
        elif hand_count < 16:
            action = 'draw'
            draw_count = random.randint(1, 3)
            return (action, draw_count, None)
        elif hand_count < 20:
            action = 'draw'
            draw_count = random.randint(0, 1)
            return (action, draw_count, None)
        else:
            return ('pass', None, None)


    def choose_second_action(self, game_state: Dict, first_action: str) -> Tuple[str, Optional[int], Optional[Player]]:
        if len(game_state['current_player'].cards) > 19:
            return ('pass', None, None)

        my_hand = CollectionOfCards(game_state['current_player'].cards)
        hand_count = len(my_hand.collection)
        my_largest_group = my_hand.largest_valid_group()

        if first_action == 'draw':
            worthy_target = []
            for player in game_state['other_players']:
                # player_count = len(player.hand)
                player_hand = CollectionOfCards(player.cards)
                worthy_or_not = False
                for card in player_hand.collection:
                    my_hand.collection.append(card)
                    new_largest_group = my_hand.largest_valid_group()
                    if my_largest_group != None and new_largest_group != None:
                        if len(new_largest_group) > len(my_largest_group):
                            worthy_or_not = True
                    elif my_largest_group == None and new_largest_group != None:
                        worthy_or_not = True
                    my_hand.collection.pop()
                if worthy_or_not == True:
                    worthy_target.append(player)

            if worthy_target != []:
                if len(worthy_target) == 2:
                    player_a = game_state['other_players'][0]
                    player_b = game_state['other_players'][1]
                    player_a_count = len(player_a.cards)
                    player_b_count = len(player_b.cards)
                    target_player = None
                    if player_a_count > player_b_count and player_a_count > hand_count:
                        target_player = player_a

                    if player_a_count < player_b_count and player_b_count > hand_count:
                        target_player = player_b

                    if player_a_count == player_b_count and player_b_count > hand_count:
                        target_player = random.choice(worthy_target)

                    if target_player is not None:
                        return ('take', None, target_player)
                else:
                    other_player = worthy_target[0]
                    other_player_count = len(other_player.cards)
                    if other_player_count > hand_count:
                        action = 'take'
                        return (action, None, other_player)
            return ('pass', None, None)


        elif first_action == 'take':
            if hand_count < 8:
                action = 'draw'
                return (action, 3, None)
            elif hand_count < 16:
                action = 'draw'
                draw_count = random.randint(1, 3)
                return (action, draw_count, None)
            elif hand_count < 20:
                action = 'draw'
                draw_count = random.randint(0, 1)
                return (action, draw_count, None)
            else:
                return ('pass', None, None)

    def get_strategy_name(self) -> str:
        return "AGGRESSIVE"
