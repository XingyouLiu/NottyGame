import sys
import os

sys.stderr.flush()

# 获取 sys.stderr 的文件描述符
stderr_fd = sys.stderr.fileno()

# 打开 os.devnull（在 Unix 系统上是 '/dev/null'，在 Windows 上是 'nul'）
devnull = os.open(os.devnull, os.O_WRONLY)

# 使用 os.dup2 将 stderr 重定向到 devnull
os.dup2(devnull, stderr_fd)

from pyscipopt import Model
from collections import defaultdict, Counter
from typing import List, Tuple, Optional
from card import Card
from itertools import combinations
from typing import List, Tuple, Dict, Set, Optional
import time

class CollectionOfCards:
    def __init__(self, cards: List[Card]) -> None:
        self.collection = cards


    def is_valid_group(self) -> bool:
        if len(self.collection) < 3: 
            return False
        
        valid_condition_1, valid_condition_2 = False, False  

        numbers_list = []
        colours_list = []
        for card in self.collection:
            numbers_list.append(card.number)
            colours_list.append(card.color)
        numbers_set, colours_set = set(numbers_list), set(colours_list)

        if len(colours_set) == 1 and len(numbers_set) >= 3 and len(numbers_list) == len(numbers_set):
            sorted_numbers = sorted(numbers_list)
            numbers_count = len(sorted_numbers)
            for i in range(1, len(sorted_numbers)):
                if sorted_numbers[i - 1] + 1 != sorted_numbers[i]:
                    break
                if i == numbers_count - 1:
                    valid_condition_1 = True

        if len(numbers_set) == 1 and len(colours_set) >= 3 and len(colours_set) == len(colours_list):
            valid_condition_2 = True

        return valid_condition_1 or valid_condition_2


    def exist_valid_group(self) -> bool:
        colour_number_dict: Dict[str, List[int]] = {}
        number_colour_dict: Dict[int, Set[str]] = {}
        for card in self.collection:
            colour, number = card.color, card.number
            if colour not in colour_number_dict:
                colour_number_dict[colour] = [number]
            else:
                colour_number_dict[colour].append(number)
            if number not in number_colour_dict:
                number_colour_dict[number] = {colour}
            else:
                number_colour_dict[number].add(colour)

        for numbers_list in colour_number_dict.values():
            sorted_numbers = sorted(list(set((numbers_list))))
            num_length = len(sorted_numbers)

            if num_length < 3:
                continue
            count = 1

            for i in range(1, num_length):
                if sorted_numbers[i - 1] + 1 == sorted_numbers[i]:
                    count += 1
                    if count == 3:
                        return True
                else:
                    count = 1

        for colours_set in number_colour_dict.values():
            if len(colours_set) >= 3:
                return True

        return False
    

    def largest_valid_group(self) -> Optional[List[Card]]:
        largest_valid_group: Optional[List[Card]] = None
        largest_length: int = 0  

        colour_number_dict: Dict[str, List[int]] = {}  
        number_colour_dict: Dict[int, Set[str]] = {}  
        for card in self.collection:  
            colour, number = card.color, card.number                    
            if colour not in colour_number_dict:
                colour_number_dict[colour] = [number]
            else:
                colour_number_dict[colour].append(number)
            if number not in number_colour_dict:
                number_colour_dict[number] = {colour}
            else:
                number_colour_dict[number].add(colour)

        colour_with_longest_sequence = None                    
        longest_sequence = []  

        for colour, numbers_list in colour_number_dict.items():
            sorted_numbers = sorted(list(set(numbers_list)))   
            num_length = len(sorted_numbers)
            if num_length < 3:  
                continue

            i = 1
            while i < num_length:                     
                count = 1                                      
                j = i                                          
                while j < num_length and sorted_numbers[j-1] + 1 == sorted_numbers[j]:
                    count += 1
                    j += 1
                if count > largest_length:
                    largest_length = count                   
                    colour_with_longest_sequence = colour    
                    longest_sequence = sorted_numbers[j - largest_length: j]  

                if j > i:    
                    i = j
                else:        
                    i += 1

        if largest_length >= 3:
            largest_valid_group = [(colour_with_longest_sequence, num) for num in longest_sequence]

        for number, colours_set in number_colour_dict.items():
            colours_length = len(colours_set)
            if colours_length >= 3 and colours_length > largest_length:
                largest_length = colours_length
                largest_valid_group = [(colour, number) for colour in colours_set]

        largest_valid_group_cards = []
        largest_valid_group_cards_set = set()

        if not largest_valid_group:
            return []

        for card_tuple in largest_valid_group:
            colour, number = card_tuple[0], card_tuple[1]
            for card in self.collection:
                if card.color == colour and card.number == number and (card.color, card.number) not in largest_valid_group_cards_set:
                    largest_valid_group_cards.append(card)
                    largest_valid_group_cards_set.add((card.color, card.number))

        return sorted(largest_valid_group_cards, key = lambda card: (card.number, card.color))
    

    def all_valid_groups_with_largest_length(self) -> List[List[Card]]:
        largest_length_groups: List[List[Tuple[str, int]]] = []   

        colour_number_dict: Dict[str, List[int]] = {}  
        number_colour_dict: Dict[int, Set[str]] = {}  
        for card in self.collection:  
            colour, number = card.color, card.number                    
            if colour not in colour_number_dict:
                colour_number_dict[colour] = [number]
            else:
                colour_number_dict[colour].append(number)
            if number not in number_colour_dict:
                number_colour_dict[number] = {colour}
            else:
                number_colour_dict[number].add(colour)
                   
        sequence = []  

        for colour, numbers_list in colour_number_dict.items():
            sorted_numbers = sorted(set(numbers_list))
            num_length = len(sorted_numbers)
            if num_length < 3:
                continue
            for i in range(num_length - 2):
                sequence = [sorted_numbers[i]]
                for j in range(i + 1, num_length):
                    if sorted_numbers[j] == sorted_numbers[j - 1] + 1:
                        sequence.append(sorted_numbers[j])
                        if len(sequence) >= 3:
                            largest_length_groups.append([(colour, num) for num in sequence])
                    else:
                        break

        for number, colours_set in number_colour_dict.items():
            colours_length = len(colours_set)
            if colours_length >= 3:
                largest_length_groups.append([(colour, number) for colour in colours_set])

        largest_length_groups_cards = []

        for group in largest_length_groups:
            group_cards = []
            group_set = set()
            for card_tuple in group:
                colour, number = card_tuple[0], card_tuple[1]
                for card in self.collection:
                    if card.color == colour and card.number == number and (card.color, card.number) not in group_set:
                        group_cards.append(card)
                        group_set.add((card.color, card.number))
            largest_length_groups_cards.append(group_cards)

        return sorted(largest_length_groups_cards, key = lambda group: len(group), reverse=True)
    

    def all_valid_groups(self) -> List[List[Card]]:
        valid_groups: List[List[Tuple[str, int]]] = []
        valid_groups_cards: List[List[Card]] = []

        colour_number_dict: Dict[str, List[int]] = {}
        number_colour_dict: Dict[int, Set[str]] = {}
        for card in self.collection:
            colour, number = card.color, card.number
            if colour not in colour_number_dict:
                colour_number_dict[colour] = [number]
            else:
                colour_number_dict[colour].append(number)
            if number not in number_colour_dict:
                number_colour_dict[number] = {colour}
            else:
                number_colour_dict[number].add(colour)

        for colour, numbers_list in colour_number_dict.items():
            sorted_numbers = sorted(set(numbers_list))
            num_length = len(sorted_numbers)
            if num_length < 3:
                continue
            for start in range(num_length):
                current_sequence = [sorted_numbers[start]]
                for end in range(start + 1, num_length):
                    if sorted_numbers[end] == sorted_numbers[end - 1] + 1:
                        current_sequence.append(sorted_numbers[end])
                        if len(current_sequence) >= 3:
                            valid_groups.append([(colour, num) for num in current_sequence.copy()])
                    else:
                        break  

        for number, colours_set in number_colour_dict.items():
            colours_list = list(colours_set)
            colours_length = len(colours_list)
            if colours_length >= 3:
                for r in range(3, colours_length + 1):
                    for colour_combo in combinations(colours_list, r):
                        group = [(colour, number) for colour in colour_combo]
                        valid_groups.append(group)

        
        for group in valid_groups:
            group_cards = []
            group_set = set()
            for card_tuple in group:
                colour, number = card_tuple[0], card_tuple[1]
                for card in self.collection:
                    if card.color == colour and card.number == number and (card.color, card.number) not in group_set:
                        group_cards.append(card)
                        group_set.add((card.color, card.number))
            valid_groups_cards.append(group_cards)

        return sorted(valid_groups_cards, key = lambda group: len(group), reverse=True)
    

    def find_best_discard_2(self):
        """Find the best group to discard"""
        cards = self.collection

        def generate_no_repeat_card_groups(groups_in_tuple: List[List[Tuple[str, int]]]) -> List[List[Card]]:
            """Turn the tuple groups into card groups without repeated card objects"""
            used_cards = set()
            card_groups = []
            for group in groups_in_tuple:
                current_group_cards = []
                for card_tuple in group:
                    for card in cards:
                        if (card.color, card.number) == card_tuple and card not in used_cards:
                            current_group_cards.append(card)
                            used_cards.add(card)
                            break
                card_groups.append(current_group_cards)
            return card_groups
        
        '''
        groups_with_largest_length = self.all_valid_groups_with_largest_length()
        n = len(groups_with_largest_length)

        if n == 1:             #If there is only one group in groups with largest length, then this is the best group to discard
            return groups_with_largest_length, len(groups_with_largest_length[0])
        '''

        hand = []
        for card in cards:
            hand.append((card.color, card.number))
        hand_counts = Counter(hand)                     #Count the number of each card in hand

        valid_card_groups = self.all_valid_groups()

        n = len(valid_card_groups)

        if n == 1:             #If there is only one group in all valid groups, then this is the best group to discard
            return valid_card_groups, len(valid_card_groups[0])
        
        card_repeat_in_groups = False                    #Check if there is any card repeated (two groups have to use the same card in hand) in groups with largest length
        all_card_tuple_in_groups = [(card.color, card.number) for group in valid_card_groups for card in group]
        card_tuple_counts = Counter(all_card_tuple_in_groups)
        for card_tuple, count in card_tuple_counts.items():
            if card_tuple in hand_counts:
                if count > hand_counts[card_tuple]:
                    card_repeat_in_groups = True
                    break

        if not card_repeat_in_groups:                    #If there is no card repeated, directly discard all groups 
            card_count = 0
            groups_in_tuple = []
            for group in valid_card_groups:
                groups_in_tuple.append([(card.color, card.number) for card in group])
                card_count += len(group)
            
            card_groups = generate_no_repeat_card_groups(groups_in_tuple)           
            return card_groups, card_count
        
        '''
        #If there exists repeated cards, and all groups have 3 cards                
        max_count_in_group = 0                                                      
        for group in valid_card_groups:        
            max_count_in_group = max(max_count_in_group, len(group))
        if max_count_in_group == 3:                        
            if n == 2:                                     #If there are only two groups, each group has 3 cards, simply discard one of them
                return [valid_card_groups[0]], 3  
            else:                                         #If there are more than two groups, find the best subset of groups to discard. There should be no repeated cards (two groups have to use the same card in hand) in the subset.
                groups_in_tuple = []
                for group in valid_card_groups:
                    groups_in_tuple.append([(card.color, card.number) for card in group])
                
                for size in range(n, 0, -1):              #List all possible subsets of groups, from the largest to the smallest
                    for subset_indices in combinations(range(n), size):
                        subset = [groups_in_tuple[i] for i in subset_indices]
                        tuple_counter = Counter(t for lst in subset for t in lst)
                        valid = True
                        for t, count in tuple_counter.items():
                            if t not in hand_counts or count > hand_counts[t]:   #If the number of this card in the subset is more than in hand, then there are repeated cards in the subset, no need to check further
                                valid = False
                                break

                        if valid:
                            subset_cards = generate_no_repeat_card_groups(subset)
                            return subset_cards, len(subset) * 3
        '''

        #If there exists repeated cards, and some groups have more than 3 cards, use linear programming to find the best combination of groups to discard                  
        valid_groups = []
        for group in valid_card_groups:
            valid_groups.append([(card.color, card.number) for card in group])


        model = Model("Maximize_Discarded_Cards")  #Create a maximization problem
        model.setParam('display/verblevel', 0)

        group_vars = {}
        for i, group in enumerate(valid_groups):
            var = model.addVar(name=f"group_{i}", vtype='binary')
            group_vars[i] = var

        group_card_counts = [len(group) for group in valid_groups]

        objective = sum([group_card_counts[i] * group_vars[i] for i in range(len(valid_groups))])
        model.setObjective(objective, sense = 'maximize')   #Objective function

        card_usage = defaultdict(list)
        for i, group in enumerate(valid_groups):
            for card in group:
                card_usage[card].append(group_vars[i])

        for card, vars_list in card_usage.items():
            model.addCons(sum(vars_list) <= hand_counts.get(card, 0), f"Constraint_{card}")   #Add constraints

        model.optimize()     #Solve the problem
        
        #Extract the selected groups
        selected_groups = [] 
        total_discarded = 0
        for i, var in group_vars.items():
            if model.getVal(var) == 1:
                selected_groups.append(valid_groups[i])
                total_discarded += group_card_counts[i]

        selected_card_groups = generate_no_repeat_card_groups(selected_groups)
        return selected_card_groups, total_discarded


    def find_best_discard(self):
        """Find the best group to discard"""
        cards = self.collection

        def generate_no_repeat_card_groups(groups_in_tuple: List[List[Tuple[str, int]]]) -> List[List[Card]]:
            """Turn the tuple groups into card groups without repeated card objects"""
            used_cards = set()
            card_groups = []
            for group in groups_in_tuple:
                current_group_cards = []
                for card_tuple in group:
                    for card in cards:
                        if (card.color, card.number) == card_tuple and card not in used_cards:
                            current_group_cards.append(card)
                            used_cards.add(card)
                            break
                card_groups.append(current_group_cards)
            return card_groups
        
        '''
        groups_with_largest_length = self.all_valid_groups_with_largest_length()
        n = len(groups_with_largest_length)

        if n == 1:             #If there is only one group in groups with largest length, then this is the best group to discard
            return groups_with_largest_length, len(groups_with_largest_length[0])
        '''

        hand = []
        for card in cards:
            hand.append((card.color, card.number))
        hand_counts = Counter(hand)                     #Count the number of each card in hand

        valid_card_groups = self.all_valid_groups()

        n = len(valid_card_groups)

        if n == 1:             #If there is only one group in all valid groups, then this is the best group to discard
            return valid_card_groups, len(valid_card_groups[0])
        
        card_repeat_in_groups = False                    #Check if there is any card repeated (two groups have to use the same card in hand) in groups with largest length
        all_card_tuple_in_groups = [(card.color, card.number) for group in valid_card_groups for card in group]
        card_tuple_counts = Counter(all_card_tuple_in_groups)
        for card_tuple, count in card_tuple_counts.items():
            if card_tuple in hand_counts:
                if count > hand_counts[card_tuple]:
                    card_repeat_in_groups = True
                    break

        if not card_repeat_in_groups:                    #If there is no card repeated, directly discard all groups 
            card_count = 0
            groups_in_tuple = []
            for group in valid_card_groups:
                groups_in_tuple.append([(card.color, card.number) for card in group])
                card_count += len(group)
            
            card_groups = generate_no_repeat_card_groups(groups_in_tuple)           
            return card_groups, card_count
        
        #If there exists repeated cards, and all groups have 3 cards                
        max_count_in_group = 0                                                      
        for group in valid_card_groups:        
            max_count_in_group = max(max_count_in_group, len(group))
        if max_count_in_group == 3:                        
            if n == 2:                                     #If there are only two groups, each group has 3 cards, simply discard one of them
                return [valid_card_groups[0]], 3  
            else:                                         #If there are more than two groups, find the best subset of groups to discard. There should be no repeated cards (two groups have to use the same card in hand) in the subset.
                groups_in_tuple = []
                for group in valid_card_groups:
                    groups_in_tuple.append([(card.color, card.number) for card in group])
                
                for size in range(n, 0, -1):              #List all possible subsets of groups, from the largest to the smallest
                    for subset_indices in combinations(range(n), size):
                        subset = [groups_in_tuple[i] for i in subset_indices]
                        tuple_counter = Counter(t for lst in subset for t in lst)
                        valid = True
                        for t, count in tuple_counter.items():
                            if t not in hand_counts or count > hand_counts[t]:   #If the number of this card in the subset is more than in hand, then there are repeated cards in the subset, no need to check further
                                valid = False
                                break

                        if valid:
                            subset_cards = generate_no_repeat_card_groups(subset)
                            return subset_cards, len(subset) * 3

        #If there exists repeated cards, and some groups have more than 3 cards, use linear programming to find the best combination of groups to discard                  
        valid_groups = []
        for group in valid_card_groups:
            valid_groups.append([(card.color, card.number) for card in group])


        model = Model("Maximize_Discarded_Cards")  #Create a maximization problem
        model.setParam('display/verblevel', 0)

        group_vars = {}
        for i, group in enumerate(valid_groups):
            var = model.addVar(name=f"group_{i}", vtype='binary')
            group_vars[i] = var

        group_card_counts = [len(group) for group in valid_groups]

        objective = sum([group_card_counts[i] * group_vars[i] for i in range(len(valid_groups))])
        model.setObjective(objective, sense = 'maximize')   #Objective function

        card_usage = defaultdict(list)
        for i, group in enumerate(valid_groups):
            for card in group:
                card_usage[card].append(group_vars[i])

        for card, vars_list in card_usage.items():
            model.addCons(sum(vars_list) <= hand_counts.get(card, 0), f"Constraint_{card}")   #Add constraints

        model.optimize()     #Solve the problem
        
        #Extract the selected groups
        selected_groups = [] 
        total_discarded = 0
        for i, var in group_vars.items():
            if model.getVal(var) == 1:
                selected_groups.append(valid_groups[i])
                total_discarded += group_card_counts[i]

        selected_card_groups = generate_no_repeat_card_groups(selected_groups)
        return selected_card_groups, total_discarded
    

    def only_use_model(self):

        cards = self.collection

        def generate_no_repeat_card_groups(groups_in_tuple: List[List[Tuple[str, int]]]) -> List[List[Card]]:
            """Turn the tuple groups into card groups without repeated card objects"""
            used_cards = set()
            card_groups = []
            for group in groups_in_tuple:
                current_group_cards = []
                for card_tuple in group:
                    for card in cards:
                        if (card.color, card.number) == card_tuple and card not in used_cards:
                            current_group_cards.append(card)
                            used_cards.add(card)
                            break
                card_groups.append(current_group_cards)
            return card_groups

        valid_card_groups = self.all_valid_groups()       
        valid_groups = []
        for group in valid_card_groups:
            valid_groups.append([(card.color, card.number) for card in group])

        hand = []
        for card in cards:
            hand.append((card.color, card.number))
        hand_counts = Counter(hand) 

        model = Model("Maximize_Discarded_Cards")  #Create a maximization problem
        model.setParam('display/verblevel', 0)

        group_vars = {}
        for i, group in enumerate(valid_groups):
            var = model.addVar(name=f"group_{i}", vtype='binary')
            group_vars[i] = var

        group_card_counts = [len(group) for group in valid_groups]

        objective = sum([group_card_counts[i] * group_vars[i] for i in range(len(valid_groups))])
        model.setObjective(objective, sense = 'maximize')   #Objective function

        card_usage = defaultdict(list)
        for i, group in enumerate(valid_groups):
            for card in group:
                card_usage[card].append(group_vars[i])

        for card, vars_list in card_usage.items():
            model.addCons(sum(vars_list) <= hand_counts.get(card, 0), f"Constraint_{card}")   #Add constraints

        model.optimize()     #Solve the problem
        
        #Extract the selected groups
        selected_groups = [] 
        total_discarded = 0
        for i, var in group_vars.items():
            if model.getVal(var) == 1:
                selected_groups.append(valid_groups[i])
                total_discarded += group_card_counts[i]

        selected_card_groups = generate_no_repeat_card_groups(selected_groups)
        return selected_card_groups, total_discarded
    

'''
    def find_best_discard(self):
        """Find the best group to discard"""
        cards = self.collection

        def generate_no_repeat_card_groups(groups_in_tuple: List[List[Tuple[str, int]]]) -> List[List[Card]]:
            """Turn the tuple groups into card groups without repeated card objects"""
            used_cards = set()
            card_groups = []
            for group in groups_in_tuple:
                current_group_cards = []
                for card_tuple in group:
                    for card in cards:
                        if (card.color, card.number) == card_tuple and card not in used_cards:
                            current_group_cards.append(card)
                            used_cards.add(card)
                            break
                card_groups.append(current_group_cards)
            return card_groups
        
        groups_with_largest_length = self.all_valid_groups_with_largest_length()
        n = len(groups_with_largest_length)

        if n == 1:             #If there is only one group in groups with largest length, then this is the best group to discard
            return groups_with_largest_length, len(groups_with_largest_length[0])
        
        hand = []
        for card in cards:
            hand.append((card.color, card.number))
        hand_counts = Counter(hand)                     #Count the number of each card in hand
        
        card_repeat_in_groups = False                    #Check if there is any card repeated (two groups have to use the same card in hand) in groups with largest length
        all_card_tuple_in_groups = [(card.color, card.number) for group in groups_with_largest_length for card in group]
        card_tuple_counts = Counter(all_card_tuple_in_groups)
        for card_tuple, count in card_tuple_counts.items():
            if card_tuple in hand_counts:
                if count > hand_counts[card_tuple]:
                    card_repeat_in_groups = True
                    break

        if not card_repeat_in_groups:                    #If there is no card repeated, directly discard all groups 
            card_count = 0
            groups_in_tuple = []
            for group in groups_with_largest_length:
                groups_in_tuple.append([(card.color, card.number) for card in group])
                card_count += len(group)
            
            card_groups = generate_no_repeat_card_groups(groups_in_tuple)           
            return card_groups, card_count

        #If there exists repeated cards, and all groups have 3 cards                
        max_count_in_group = 0                                                      
        for group in groups_with_largest_length:        
            max_count_in_group = max(max_count_in_group, len(group))
        if max_count_in_group == 3:                        
            if n == 2:                                     #If there are only two groups, each group has 3 cards, simply discard one of them
                return [groups_with_largest_length[0]], 3  
            else:                                         #If there are more than two groups, find the best subset of groups to discard. There should be no repeated cards (two groups have to use the same card in hand) in the subset.
                groups_in_tuple = []
                for group in groups_with_largest_length:
                    groups_in_tuple.append([(card.color, card.number) for card in group])
                
                for size in range(n, 0, -1):              #List all possible subsets of groups, from the largest to the smallest
                    for subset_indices in combinations(range(n), size):
                        subset = [groups_in_tuple[i] for i in subset_indices]
                        tuple_counter = Counter(t for lst in subset for t in lst)
                        valid = True
                        for t, count in tuple_counter.items():
                            if t not in hand_counts or count > hand_counts[t]:   #If the number of this card in the subset is more than in hand, then there are repeated cards in the subset, no need to check further
                                valid = False
                                break

                        if valid:
                            subset_cards = generate_no_repeat_card_groups(subset)
                            return subset_cards, len(subset) * 3

        #If there exists repeated cards, and some groups have more than 3 cards, use linear programming to find the best combination of groups to discard           
        valid_card_groups = self.all_valid_groups()       
        valid_groups = []
        for group in valid_card_groups:
            valid_groups.append([(card.color, card.number) for card in group])

        model = Model("Maximize_Discarded_Cards")  #Create a maximization problem
        model.setParam('display/verblevel', 0)

        group_vars = {}
        for i, group in enumerate(valid_groups):
            var = model.addVar(name=f"group_{i}", vtype='binary')
            group_vars[i] = var

        group_card_counts = [len(group) for group in valid_groups]

        objective = sum([group_card_counts[i] * group_vars[i] for i in range(len(valid_groups))])
        model.setObjective(objective, sense = 'maximize')   #Objective function

        card_usage = defaultdict(list)
        for i, group in enumerate(valid_groups):
            for card in group:
                card_usage[card].append(group_vars[i])

        for card, vars_list in card_usage.items():
            model.addCons(sum(vars_list) <= hand_counts.get(card, 0), f"Constraint_{card}")   #Add constraints

        model.optimize()     #Solve the problem
        
        #Extract the selected groups
        selected_groups = [] 
        total_discarded = 0
        for i, var in group_vars.items():
            if model.getVal(var) == 1:
                selected_groups.append(valid_groups[i])
                total_discarded += group_card_counts[i]

        selected_card_groups = generate_no_repeat_card_groups(selected_groups)
        return selected_card_groups, total_discarded
'''

    
    



'''
card0 = Card('red', 3)
card1 = Card('red', 1)
card2 = Card('red', 2)
card3 = Card('red', 1)
card5 = Card('blue', 1)
card6 = Card('yellow', 1)
card8 = Card('blue', 2)
card9 = Card('green', 4)
card10 = Card('blue', 2)
card20 = Card('yellow', 2)
card11 = Card('green', 3)
card12 = Card('green', 10)
card13 = Card('red', 4)
card14 = Card('red', 5)
card15 = Card('red', 6)

collection = CollectionOfCards([card0, card1, card2, card5, card6, card8, card9, card10, card11, card12, card13, card14, card15, card20])

for group in collection.all_valid_groups_with_largest_length():
    print([(card.color, card.number) for card in group])

print('************************************')
print(collection.find_best_discard()[1])
for group in collection.find_best_discard()[0]:
    print([(card.color, card.number) for card in group])
'''

'''
card0 = Card('red', 3)
card1 = Card('red', 1)
card2 = Card('red', 2)
card3 = Card('red', 1)
card5 = Card('blue', 1)
card6 = Card('yellow', 1)
card8 = Card('blue', 2)
card9 = Card('green', 3)
card10 = Card('blue', 2)
card20 = Card('yellow', 2)
card11 = Card('green', 3)
card12 = Card('green', 10)
card13 = Card('red', 3)
card14 = Card('blue', 3)
card15 = Card('red', 6)

collection = CollectionOfCards([card0, card1, card2, card3, card5, card6, card8, card9, card10, card11, card12, card13, card14, card15, card20])

for group in collection.all_valid_groups_with_largest_length():
    print([(card.color, card.number) for card in group])

print('************************************')

print(collection.find_best_discard()[1])
for group in collection.find_best_discard()[0]:
    print([(card.color, card.number) for card in group])
'''

'''
import random
from collections import Counter
from itertools import combinations
from card import Card

def generate_random_hand():
    colors = ['red', 'blue', 'yellow', 'green']
    numbers = list(range(1, 11))
    hand = []
    for _ in range(20):
        color = random.choice(colors)
        number = random.choice(numbers)
        hand.append(Card(color, number))
    return hand

def test_find_best_discard():
    num_tests = 1000  
    error_count = 0
    for test_num in range(num_tests):
        hand = generate_random_hand()
        collection = CollectionOfCards(hand)
        try:
            selected_card_groups, total_discarded = collection.find_best_discard()
        except Exception as e:
            print(f"测试 {test_num} 出现异常：{e}")
            continue

        # 检查所有选中的牌对象都在手牌中
        all_selected_cards = [card for group in selected_card_groups for card in group]
        if not all(card in hand for card in all_selected_cards):
            print(f"错误测试 {test_num}：选中的牌对象不在手牌中。")
            print(f"手牌: {hand}")
            print(f"选中的牌: {all_selected_cards}")
            error_count += 1
            continue

        # 检查是否有牌对象在不同的组中重复使用
        selected_card_ids = [id(card) for card in all_selected_cards]
        if len(selected_card_ids) != len(set(selected_card_ids)):
            print(f"错误测试 {test_num}：同一个牌对象在不同的组中重复使用。")
            print(f"手牌: {[card.color + str(card.number) for card in hand]}")
            print(f"选中的牌: {[card.color + str(card.number) for card in all_selected_cards]}")
            error_count += 1
            continue

    print(f"测试完成，共有 {error_count} 个错误，测试次数 {num_tests} 次。")

if __name__ == '__main__':
    test_find_best_discard()
'''

'''
card1, card2, card3, card4, card5, card6, card7, card8 = Card('yellow', 6), Card('yellow', 7), Card('yellow', 8), Card('yellow', 9), Card('yellow', 10), Card('yellow', 7), Card('yellow', 8), Card('yellow', 9)
collection = CollectionOfCards([card1, card2, card3, card4, card5, card6, card7, card8])
print([[card.color + str(card.number) for card in group] for group in collection.all_valid_groups_with_largest_length()])
print([[card.color + str(card.number) for card in group] for group in collection.all_valid_groups()])
'''

'''
import random
from collections import Counter
from itertools import combinations
from card import Card

def generate_random_hand():
    colors = ['red', 'blue', 'yellow', 'green']
    numbers = list(range(1, 11))
    hand = []
    for _ in range(13):
        color = random.choice(colors)
        number = random.choice(numbers)
        hand.append(Card(color, number))
    return hand

def test_find_best_discard():
    num_tests = 1000  
    error_count = 0
    for test_num in range(num_tests):
        hand = generate_random_hand()
        collection = CollectionOfCards(hand)
        try:
            selected_card_groups, total_discarded = collection.find_best_discard_2()
            selected_card_groups2, total_discarded2 = collection.only_use_model()
        except Exception as e:
            print(f"测试 {test_num} 出现异常：{e}")
            continue

        # 检查算法正确性
        if total_discarded != total_discarded2:
            print(f"错误测试 {test_num}：算法正确性错误。")
            print(f"手牌: {[card.color + str(card.number) for card in hand]}")
            print(f"算法1选中的牌: {[card.color + str(card.number) for group in selected_card_groups for card in group]}")
            print(f"算法2选中的牌: {[card.color + str(card.number) for group in selected_card_groups2 for card in group]}")
            error_count += 1
            continue

    print(f"测试完成，共有 {error_count} 个错误，测试次数 {num_tests} 次。")

if __name__ == '__main__':
    test_find_best_discard()


'''

'''
import random
from collections import Counter
from itertools import combinations
from card import Card

def generate_random_hand():
    colors = ['red', 'blue', 'yellow', 'green']
    numbers = list(range(1, 11))
    hand = []
    for _ in range(20):
        color = random.choice(colors)
        number = random.choice(numbers)
        hand.append(Card(color, number))
    return hand


def test_which_is_faster():
    num_tests = 1000
    time_1, time_2, time_3 = 0, 0, 0
    for _ in range(num_tests):
        hand = generate_random_hand()
        collection = CollectionOfCards(hand)
        start_time = time.time()
        collection.find_best_discard()
        time_1 += time.time() - start_time
    
    for _ in range(num_tests):
        hand = generate_random_hand()
        collection = CollectionOfCards(hand)
        start_time = time.time()
        collection.find_best_discard_2()
        time_2 += time.time() - start_time

    for _ in range(num_tests):
        hand = generate_random_hand()
        collection = CollectionOfCards(hand)
        start_time = time.time()
        collection.only_use_model()
        time_3 += time.time() - start_time

    print(f"find_best_discard: {time_1 / num_tests}")
    print(f"find_best_discard_2: {time_2 / num_tests}")
    print(f"only_use_model: {time_3 / num_tests}")

if __name__ == '__main__':
    test_which_is_faster()
'''

