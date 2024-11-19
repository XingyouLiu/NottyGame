from typing import List, Tuple, Dict, Set, Optional

class CollectionOfCards:
    def __init__(self, cards_list: List[Tuple[str, int]]) -> None:
        self.collection = cards_list


    def is_valid_group(self) -> bool:
        if len(self.collection) < 3: 
            return False
        
        valid_condition_1, valid_condition_2 = False, False  

        numbers_list = []
        colours_list = []
        for card in self.collection:
            numbers_list.append(card[1])
            colours_list.append(card[0])
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
            colour, number = card[0], card[1]
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
    

    def largest_valid_group(self) -> Optional[List[Tuple[str, int]]]:
        largest_valid_group: Optional[List[Tuple[str, int]]] = None
        largest_length: int = 0  

        colour_number_dict: Dict[str, List[int]] = {}  
        number_colour_dict: Dict[int, Set[str]] = {}  
        for card in self.collection:  
            colour, number = card[0], card[1]                    
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
            largest_valid_group = sorted([(colour_with_longest_sequence, num) for num in longest_sequence], key=lambda x: x[1])

        for number, colours_set in number_colour_dict.items():
            colours_length = len(colours_set)
            if colours_length >= 3 and colours_length > largest_length:
                largest_length = colours_length
                largest_valid_group = sorted([(colour, number) for colour in colours_set], key=lambda x: x[0])

        return largest_valid_group
    

    def all_valid_groups_with_largest_length(self) -> List[List[Tuple[str, int]]]:
        largest_length_groups: List[List[Tuple[str, int]]] = []   

        colour_number_dict: Dict[str, List[int]] = {}  
        number_colour_dict: Dict[int, Set[str]] = {}  
        for card in self.collection:  
            colour, number = card[0], card[1]                    
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
                largest_length_groups.append(sorted([(colour, number) for colour in colours_set], key=lambda x: x[0]))

        return sorted(largest_length_groups, key=lambda x: len(x), reverse=True)
    

    @staticmethod
    def probability_exist_valid_group_drawing_one_from_deck(hands_of_players: List['CollectionOfCards']) -> float:
        last_player_hand = hands_of_players[-1]
        if last_player_hand.exist_valid_group():              
            return 1

        cards_in_players_hands_count: Dict[Tuple[str, int], int] = {}                     
        for colour in {'red', 'blue', 'green', 'yellow'}:
            for number in range(1, 11):
                cards_in_players_hands_count[(colour, number)] = 0

        for hand in hands_of_players:
            for card in hand.collection:
                colour, number = card[0], card[1]
                if cards_in_players_hands_count[(colour, number)] == 0:    
                    cards_in_players_hands_count[(colour, number)] = 1
                elif cards_in_players_hands_count[(colour, number)] == 1:  
                    cards_in_players_hands_count[(colour, number)] = 2
                else:
                    raise ValueError("Invalid input: The player's hand exceeds the card limit!") 

        remaining_cards_count, can_form_valid_group_count = 0, 0   
        for card, count in cards_in_players_hands_count.items():   
            if count < 2:                                          
                remaining_cards_count += (2 - count)               
                last_player_hand.collection.append((card[0], card[1]))  
                if last_player_hand.exist_valid_group():                      
                    can_form_valid_group_count += (2 - count)
                last_player_hand.collection.pop()                            

        return can_form_valid_group_count / remaining_cards_count
    

    def probability_exist_valid_group_drawing_from_another(hands_of_players: List['CollectionOfCards']) -> float:
        last_player_hand = hands_of_players[-1]
        if last_player_hand.exist_valid_group():              
            return 1
        
        other_players_hands = hands_of_players[:-1]

        cards_in_other_players_hands_count: Dict[Tuple[str, int], int] = {}                    
        for hand in other_players_hands:
            for card in hand.collection:
                colour, number = card[0], card[1]
                if cards_in_other_players_hands_count[(colour, number)] == 0:    
                    cards_in_other_players_hands_count[(colour, number)] = 1
                elif cards_in_other_players_hands_count[(colour, number)] == 1:  
                    cards_in_other_players_hands_count[(colour, number)] = 2
                else:
                    raise ValueError("Invalid input: The player's hand exceeds the card limit!") 

        other_players_cards_count, can_form_valid_group_count = 0, 0   
        for card, count in cards_in_other_players_hands_count.items():   
            other_players_cards_count += count                                                      
            last_player_hand.collection.append((card[0], card[1]))  
            if last_player_hand.exist_valid_group():                      
                can_form_valid_group_count += count
            last_player_hand.collection.pop()                            

        return can_form_valid_group_count / other_players_cards_count
