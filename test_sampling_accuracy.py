import random
from player import Player
from card import Card
import time
from typing import Dict
import statistics
from itertools import combinations
import math
from collection_of_cards import CollectionOfCards

def create_test_game_state(deck_size: int = 30) -> Dict:
    all_cards = [
        Card(colour, number, card_width=60, card_height=90, position=(0, 0))
        for colour in {'red', 'blue', 'green', 'yellow'} 
        for number in range(1, 11)
        for _ in range(2)
    ]
    random.shuffle(all_cards)
    
    current_player = Player("current", False)
    for _ in range(15):
        current_player.add_card(all_cards.pop())
    
    deck_cards = all_cards[:deck_size]
    
    return {
        'current_player': current_player,
        'deck_cards': deck_cards,
        'deck_size': len(deck_cards),
        'other_players': []
    }

def calculate_relative_error(sampling_value: float, exact_value: float) -> float:
    if exact_value == 0:
        return 0 if sampling_value == 0 else 100.0
    return abs((sampling_value - exact_value) / exact_value) * 100


def calculate_exact_expectation(game_state: Dict) -> float:
    collection = CollectionOfCards(game_state['current_player'].cards.copy())
    draw_expected_value = 0
    draw_count = 3
    
    combination_count = math.factorial(game_state['deck_size']) // (
        math.factorial(draw_count) * math.factorial(game_state['deck_size'] - draw_count))
    
    for combination in combinations(game_state['deck_cards'], draw_count):
        for card in combination:
            collection.collection.append(card)
        if collection.exist_valid_group():
            draw_expected_value += collection.find_best_discard()[1] * 1 / combination_count
        for card in combination:
            collection.collection.pop()
    
    return draw_expected_value - draw_count

def calculate_sampling_expectation(game_state: Dict) -> float:
    collection = CollectionOfCards(game_state['current_player'].cards.copy())
    draw_expected_value = 0
    draw_count = 3
    
    combination_count = math.factorial(game_state['deck_size']) // (
        math.factorial(draw_count) * math.factorial(game_state['deck_size'] - draw_count))

    parameter = 1   
    sample_list = []
    if combination_count > 2000:
        parameter = combination_count // 1000
        sample_list = random.sample(list(combinations(game_state['deck_cards'], draw_count)), combination_count // parameter)    
        for combination in sample_list:
            for card in combination:
                collection.collection.append(card)
            if collection.exist_valid_group():
                draw_expected_value += collection.find_best_discard()[1] * 1 / combination_count
            for card in combination:
                collection.collection.pop()
    else:
        for combination in combinations(game_state['deck_cards'], draw_count):
            for card in combination:
                collection.collection.append(card)
            if collection.exist_valid_group():
                draw_expected_value += collection.find_best_discard()[1] * 1 / combination_count
            for card in combination:
                collection.collection.pop()

    return draw_expected_value * parameter - draw_count


def test_sampling_accuracy(num_tests: int = 5, deck_size: int = 60):
    """Test the accuracy of sampling estimation"""
    relative_errors = []
    sampling_times = []
    exact_times = []
    
    for i in range(num_tests):
        game_state = create_test_game_state(deck_size)
        
        start_time = time.time()
        sampling_result = calculate_sampling_expectation(game_state)
        sampling_time = time.time() - start_time
        sampling_times.append(sampling_time)
        
        start_time = time.time()
        exact_result = calculate_exact_expectation(game_state)
        exact_time = time.time() - start_time
        exact_times.append(exact_time)
        
        relative_error = calculate_relative_error(sampling_result, exact_result)
        relative_errors.append(relative_error)
        
    
    avg_error = statistics.mean(relative_errors)
    max_error = max(relative_errors)
    min_error = min(relative_errors)
    std_error = statistics.stdev(relative_errors)
    
    avg_sampling_time = statistics.mean(sampling_times)
    avg_exact_time = statistics.mean(exact_times)
    
    print(f"Average relative error: {avg_error:.2f}%")
    print(f"Maximum relative error: {max_error:.2f}%")
    print(f"Minimum relative error: {min_error:.2f}%")
    print(f"Relative error standard deviation: {std_error:.2f}%")
    print(f"\nTime comparison:")
    print(f"Average sampling time: {avg_sampling_time:.4f} seconds")
    print(f"Average exact calculation time: {avg_exact_time:.4f} seconds")
    print(f"Time improvement ratio: {avg_exact_time/avg_sampling_time:.2f}x")
    
    error_ranges = [(0, 5), (5, 10), (10, 20), (20, 30), (30, float('inf'))]
    print("\nRelative error distribution:")
    for start, end in error_ranges:
        count = sum(1 for error in relative_errors if start <= error < end)
        percentage = (count / len(relative_errors)) * 100
        if end == float('inf'):
            print(f"More than {start}%: {percentage:.1f}% ({count})")
        else:
            print(f"{start}%-{end}%: {percentage:.1f}% ({count})")

if __name__ == "__main__":
    for deck_size in range(50, 70, 10):
        print(f"When deck size is {deck_size}:")
        test_sampling_accuracy(num_tests=10, deck_size=deck_size)
        print('***********************************************')
