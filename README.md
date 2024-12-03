
# Computer Player Strategies

This game includes several computer-controlled players with different decision-making strategies. Each computer player is implemented in a dedicated class in the module `computer_player.py`:

- **X-DEFENSIVE**: Implemented in the `ExpectationValueStrategyPlayer` class.
- **X-AGGRESSIVE**: Implemented in the `ProbabilityStrategyPlayer` class.
- **DEFENSIVE**: Implemented in the `RandomStrategyPlayer` class.
- **AGGRESSIVE**: Implemented in the `RulebasedStrategyPlayer` class.

All players share the same fundamental turn structure and special rules, but also have their own unique strategies.

---

## Common Rules

### Actions Per Turn

In each round, first perform **one** of the following actions:

- **Draw** 1, 2, or 3 cards from the deck.
- **Take** 1 card from any other player's hand.
- **Pass** to end the turn immediately.

If the initial action is not **Pass**, the player may choose to perform a second action. If choosing not to, the round ends. Otherwise, player must ensure that **Draw** and **Take** actions are each performed at most once per round. 
- If the first action is **Draw**, the second action can only be **Take**.
- If the first action is **Take**, the second action can only be **Draw**.

### Discarding Strategy

When a player's hand increases (e.g., after drawing or taking a card) or its turn begins, check for **valid groups** in its hand. If valid groups exist, the `find_best_discard` method implemented in the `CollectionOfCards` class is called to determine the optimal discarding strategy.

#### Optimal Discard Strategy
The key point of the optimal discard strategy is to choose combinations of valid groups when multiple valid groups exist, allowing the player to discard the maximum number of cards without reusing the same card in hand.

**Examples:**

1. **Example 1:**
   - **Valid Groups:**
     - `{red 1, red 2, red 3, red 4}`
     - `{red 1, green 1, yellow 1}`
   - **Issue:** Only one `red 1` in hand.
   - **Optimal Strategy:** Instead of discarding the longer group `{red 1, red 2, red 3, red 4}` (discarding 4 cards and breaking the second group), discard `{red 2, red 3, red 4}` and `{red 1, green 1, yellow 1}` for a total of 6 discarded cards.

2. **Example 2:**
   - **Valid Groups:**
     - `{red 1, red 2, red 3}`
     - `{red 1, blue 1, yellow 1}`
     - `{red 3, blue 3, yellow 3}`
   - **Issue:** Discarding `{red 1, red 2, red 3}` breaks the other two groups.
   - **Optimal Strategy:** Discard `{red 1, blue 1, yellow 1}` and `{red 3, blue 3, yellow 3}` for a total of 6 discarded cards.

#### Algorithm Implementation

The `find_best_discard` method uses an optimised algorithm to traverse possible valid groups and determine the best discard strategy. The algorithm has been tested thousands of times using test scripts to ensure the accuracy of both the optimal group combinations and the largest discard count.

The algorithm involves the following steps:

##### 1. Identify All Valid Groups

Call the `all_valid_groups` method in the `Player` class in module `player.py` to identify all possible valid groups in the player's hand.

##### 2. Generate Tuple Representations

Convert each group into a list of card tuples for easy comparison.

##### 3. Handle Simple Cases

###### a. Single Valid Group

If there's only one valid group, simply discard it.

###### b. Non-Overlapping Groups of Size 3

If all valid groups have exactly 3 cards, select the largest set of groups that don't share any cards.
  
- **Search for the Largest Non-Overlapping Subset**:
```Python
for size in range(n, 0, -1):              #List all possible subsets of groups, from the largest to the smallest
    for subset_indices in combinations(range(n), size):
        subset = [valid_groups[i] for i in subset_indices]
        tuple_counter = Counter(t for lst in subset for t in lst)
        valid = True
        for t, count in tuple_counter.items():
            if t not in hand_counts or count > hand_counts[t]:   #If the number of this card in the subset is more than in hand, then there are repeated cards in the subset, no need to check further
                valid = False
                break

        if valid:
            subset_cards = generate_no_repeat_card_groups(subset)
            return subset_cards
```

##### 4. Optimise for Complex Cases

When groups have more than 3 cards or overlapping cards, formulate the problem as an **Integer Linear Programming** (ILP) problem.

###### a. Formulate the ILP Model

- **Variables**:

  Let $x_i$ be a binary variable indicating whether group $i$ is selected (1) or not (0).

- **Objective Function**:

  Maximise the total number of discarded cards:

  $\text{Maximise} \quad \sum_{i} (\text{number of cards in group } i) \times x_i$

- **Constraints**:

  Ensure that no card is used more times than it appears in the hand:

  
  $\sum_{\text{groups containing card } c} x_i \leq \text{number of } c \text{ in hand}, \quad \forall c \in \text{hand}$

###### b. Implement the ILP Model

Using the linear programming solver **SCIP** (accessed via its Python interface **PySCIPOpt**) to set up and solve the ILP model.
```Python
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
```

###### c. Extract the Optimal Groups

After solving the model, retrieve the groups selected for discarding.

##### 5. Generate Non-Repeating Card Groups

Use the `generate_no_repeat_card_groups` helper function to map the tuple representations back to actual card objects, ensuring that the same card is never used in multiple groups.

### Special Rules

#### 1. Avoid Helping Others
Players must **never choose to take a card** from another player whose hand contains **2 or fewer cards**.

#### 2. Maximum Hand Size Limit
To prevent having too many cards, actions are restricted based on the current number of cards in the player's hand:

- **Hand size > Maximum hand size - 1**: Only **Pass** is allowed.
- **Hand size > Maximum hand size - 2**: **Draw**ing 2 or 3 cards is not allowed.
- **Hand size > Maximum hand size - 3**: **Draw**ing 3 cards is not allowed.
---

## Player-Specific Strategies

## X-DEFENSIVE

### Overview

X-DEFENSIVE is a cautious and defensive computer player. In each turn, it carefully calculates the expected value of actions that reduce the number of hand cards to guide its choices, as the aim is to reduce as many cards as possible. It avoids taking unnecessary risks and prevents accumulating too many cards. Due to its highly conservative actions, observers perceive its strategy as steady and non-impulsive.

### Strategy Details

#### Expected Value Calculation

X-DEFENSIVE guides its decisions by calculating the expected value of actions that reduce the number of hand cards.
##### Draw Operation

- **Total Combinations**: The total number of combinations for drawing \( n \) cards from the remaining deck is:
  
  \[
  C = \binom{D}{n}
  \]
  
  where \( D \) is the number of remaining cards in the deck.

- **Sampling Estimation**: If the total combinations \( C \) are too large (e.g., \( C > 2000 \)), a random subset of combinations is sampled for estimation. The sampling ratio is:
  
  \[
  \text{Sampling Ratio} = \frac{1}{k}
  \]
  
  where \( k = \left\lfloor \frac{C}{1000} \right\rfloor \).

  Note: 
  1. When \( C \) is less than 2000, \( k = 1 \) and no sampling is performed.
  2. Has verified using test scripts that the error in estimating the expected value using the sampling strategy is sufficiently small compared to the exact expected value calculated without sampling. In the vast majority of cases, the error is less than 5%, and only very rarely falls within the 5%-10% range, which is an acceptable margin of error.

- **Calculate Expected Discards**:
  
  1. For each sampled combination, temporarily add it to the current hand.
  2. Check if there exists a valid group in the hand using the `exist_valid_group` method.
  3. If a valid group exists, use the `find_best_discard_count` method implemented in the `CollectionOfCards` class to calculate the number of discardable cards \( d_i \).
  4. Accumulate the expected number of discards across all combinations.

- **Expected Value Calculation**:
  
  The probability of drawing each combination is:
  
  \[
  P_i = \frac{1}{C}
  \]
  
  The total expected number of discards is:
  
  \[
  E_{\text{discard}} = \sum_i P_i \times d_i \times k
  \]
  
  where \( k \) is the sampling amplification factor.

- **Expected Hand Reduction**:
  
  \[
  E_{\text{draw}} = E_{\text{discard}} - n
  \]
  
  where \( n \) is the number of cards drawn.

##### Take Operation
- **Exclusion Target**: If a player's hand size is less than or equal to 2, X-DEFENSIVE will not consider taking a card from that player even if this action has the highest expected value. 

- **Expected Value Calculation**:
  
  1. Let \( M \) be the number of cards in the target player's hand.
  2. The probability of taking each card is:
     
     \[
     P_j = \frac{1}{M}
     \]
  
  3. For each card in the target player's hand:
     - Temporarily add it to the current hand.
     - Check for a valid group and calculate the number of discardable cards \( d_j \) using the `find_best_discard_count` method implemented in the `CollectionOfCards` class.
     - Accumulate the expected number of discards.
  
  4. The total expected number of discards is:
     
     \[
     E_{\text{discard}} = \sum_j P_j \times d_j
     \]
  
  5. The expected hand reduction is:
     
     \[
     E_{\text{take}} = E_{\text{discard}} - 1
     \]
     
     The subtraction of 1 account for the taken card.

##### Pass Operation

The expected hand reduction for passing is 0 since the number of cards remains unchanged:
  
\[
E_{\text{pass}} = 0
\]

Explanation: As the computer player will immediately discard all possible valid groups whenever valid groups exist, there wouldn't exist any valid group at this point to be discarded, so the expected reduction of **pass** action must be 0.

#### Action Selection

X-DEFENSIVE selects the action with the highest expected hand reduction among all currently available actions based on the calculated values.

#### Special Rules

- **Consecutive Pass Limit**: When the number of cards in hand is small, in most cases, the expected value of all actions are negative, except for the **pass** action, so the computer player will choose to pass repeatedly. 
Therefore, to prevent the game from stalling, if the computer player passes twice in a row, it must choose another action (draw or take) which has the highest expected value in the next turn, even if those actions have negative expected values.

---

## X-AGGRESSIVE

### Overview

X-AGGRESSIVE is a proactive and offensive computer player. In each turn, it calculates the probability of having a valid group in hand after each possible action to guide its choices. In most cases, drawing more cards increases the probability of having a valid group in the hand. Therefore, X-AGGRESSIVE tends to draw as many cards as possible when feasible.Since it tends to increase its hand size to enhance the chances of forming valid groups, observers perceive its strategy as aggressive and proactive.

### Strategy Details

#### Probability Calculation

X-AGGRESSIVE guides his decisions by calculating the probability of having a valid group in his hand after each possible action.

##### Draw Operation

- **Total Combinations**: The total number of combinations for drawing \( n \) cards from the remaining deck is:
  
  \[
  C = \binom{D}{n}
  \]
  
  where \( D \) is the number of remaining cards in the deck.

- **Iterate Through All Combinations**:
  
  1. Use `itertools.combinations` to generate all possible draw combinations efficiently.
  2. For each combination:
     - Temporarily add it to the current hand.
     - Check if there exists a valid group in the hand using the `exist_valid_group` method.
     - If a valid group exists, increment the counter \( V \).
     - Remove the combination from the hand.
  
- **Calculate Probability of Valid Group**:
  
  \[
  P_{\text{valid}} = \frac{V}{C}
  \]

##### Take Operation

- **Exclusion Target**: If a player's hand size is less than or equal to 2, X-AGGRESSIVE will not consider taking a card from that player even if this action has the highest probability of achieving a valid group.

- **Probability Calculation**:
  
  1. Let \( M \) be the number of cards in the target player's hand.
  2. For each card in the target player's hand:
     - Temporarily add it to the current hand.
     - Check for a valid group.
     - If a valid group exists, increment the counter \( V \).
     - Remove the card from the hand.
  
  3. The probability of having a valid group after taking a card is:
     
     \[
     P_{\text{valid}} = \frac{V}{M}
     \]

##### Pass Operation

The probability of having a valid group after passing is 0 since the hand does not change. Note that as the computer player will immediately discard all possible valid groups whenever valid groups exist, there wouldn't exist any valid group at this point to be discarded at this point.

#### Action Selection

X-AGGRESSIVE selects the action with the highest probability of having a valid group among all currently available actions based on the calculated probabilities.

---

## DEFENSIVE

### Overview

DEFENSIVE is a straightforward computer player with a simple strategy. In each turn, it randomly selects an action while still adhering to the common basic principles. Its actions randomly switch between aggressive and conservative and ensures remaining neither too aggressive nor too conservative.

### Strategy Details

#### Action Selection

- **Construct Action Pool**:
  
  - Based on the common rules, build the current list of available actions (e.g., draw 1 card, draw 2 cards, draw 3 cards, take 1 card from player 1, take 2 cards from player 2, pass).
  - Randomly select an action from this list.
---

## AGGRESSIVE

### Overview

AGGRESSIVE is a rule-based computer player. In each turn, if its hand size is small, it tends to draw more cards, but when taking cards, it considers whether it can significantly increase the size of its largest valid group. It shows a balance between being aggressive and conservative, and is slightly more aggressive than DEFENSIVE, especially when its hand size is small.

### Strategy Details

#### Action Selection

AGGRESSIVE's action choices are based on the following rules:

##### Decide Whether to Take a Card

- **Evaluate the Value of Taking a Card**:
  
  1. Simulate temporarily adding each of the other players' cards to its own hand.
  2. Check if adding the card increases the size of its largest valid group.
  3. If such cards exist, mark those players as "worthy targets."

- **Select Target Player**:
  
  - From the "worthy targets", choose players who have more cards than itself as targets for taking cards.
  - If multiple target players have the same number of cards and more than itself, randomly select one.

- **Execute Take Action**:
  
  - If a suitable target player is found, choose to take a card from that player.

##### Decide Whether to Draw Cards

If no "worthy targets" are found or a take action has already been performed, AGGRESSIVE decides on the number of cards to draw based on its current hand size:

- **Hand Size < 8**: Draw 3 cards.
- **Hand Size ≥ 8 and < 16**: Randomly draw 1 to 3 cards.
- **Hand Size ≥ 16 and < 20**: Randomly choose to draw 0 or 1 card.
- **Hand Size ≥ 20**: Choose to pass.
