from itertools import combinations
from typing import List, Tuple, Dict, Set, Optional
from card import Card

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
            sorted_numbers = list(set(sorted(numbers_list)))
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
                if count >= 3:   
                    sequence = sorted_numbers[j - count: j]
                    largest_length_groups.append([(colour, num) for num in sequence])

                if j > i:    
                    i = j
                else:        
                    i += 1

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
    
