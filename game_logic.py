import random
import collections

COLORS = ["Red", "Blue", "Green", "Yellow"]
NUMBERS = list(range(1, 13))
WILD_COUNT = 8
SKIP_COUNT = 4

PHASES = [
    {"sets": 2, "set_size": 3}, # Phase 1: Two sets of three
    {"sets": 1, "set_size": 3, "run": 4}, # Phase 2: One set of 3 and one run of 4
    {"sets": 1, "set_size": 4, "run": 4}, # Phase 3: One set of 4 and one run of 4
    {"run": 7}, # Phase 4: One run of 7
    {"run": 8}, # Phase 5: One run of 8
    {"run": 9}, # Phase 6: One run of 9
    {"sets": 2, "set_size": 4}, # Phase 7: Two sets of 4
    {"color": 7}, # Phase 8: 7 cards of the same color
    {"sets": 1, "set_size": 5, "set_2": 2}, # Phase 9: One set of 5 and one set of 2
    {"sets": 1, "set_size": 5, "set_2": 3}, # Phase 10: One set of 5 and one set of 3
]

class Card:
    def __init__(self, color, number):
        self.color = color  # e.g. "Red", "Blue", or None for Wild/Skip
        self.number = number  # e.g. 1..12, "Wild", or "Skip"

    def is_wild(self):
        return self.number == "Wild"

    def is_skip(self):
        return self.number == "Skip"

    def __repr__(self):
        return f"Card({self.color}, {self.number})"

def create_deck():
    deck = [Card(color, num) for color in COLORS for num in NUMBERS for _ in range(2)]
    deck += [Card(None, "Wild")] * WILD_COUNT
    deck += [Card(None, "Skip")] * SKIP_COUNT
    random.shuffle(deck)
    return deck

class Game:
    PHASES = PHASES

    def __init__(self):
        # Persistent game-wide state
        self.round = 1
        self.player_phase = 0
        self.computer_phase = 0

        # Start the first hand
        self.start_new_hand()

    def start_new_hand(self):
        """Deals a new hand but does NOT reset the player's phase progress."""
        self.deck = create_deck()
        self.discard_pile = [self.deck.pop()]

        self.player_hand = [self.deck.pop() for _ in range(10)]
        self.computer_hand = [self.deck.pop() for _ in range(10)]

        self.current_turn = "player"
        self.has_drawn = False
        self.skip_turn = False
        # Instead of a flat list of cards, store combos for each player
        # e.g. "type": "set" or "run", plus "cards": [...]
        self.played_phases = {
            "player": [],
            "computer": []
        }
        self.phase_submission_box = []
        self.selected_card_index = None
        self.phase_submitted = False

    # ------------------------------
    # Turn / Hand Management
    # ------------------------------
    def draw_card(self, player, from_discard=False):
        if self.phase_submitted:
            # Once a phase is submitted, no further drawing is allowed this turn
            return

        if player == "player" and self.current_turn == "player" and not self.has_drawn:
            if from_discard and self.discard_pile:
                self.player_hand.append(self.discard_pile.pop())
            elif self.deck:
                self.player_hand.append(self.deck.pop())
            self.has_drawn = True

        elif player == "computer" and self.current_turn == "computer":
            if self.deck:
                self.computer_hand.append(self.deck.pop())

    def select_card(self, card_index):
        if 0 <= card_index < len(self.player_hand):
            self.selected_card_index = card_index

    def discard_selected_card(self):
        if self.selected_card_index is not None and 0 <= self.selected_card_index < len(self.player_hand):
            card_index = self.selected_card_index
            self.selected_card_index = None
            self.discard_card(card_index)
            return True
        return False

    def discard_card(self, card_index):
        if 0 <= card_index < len(self.player_hand):
            card = self.player_hand.pop(card_index)
            self.discard_pile.append(card)
            self.has_drawn = False

            # Skip logic
            if card.is_skip():
                self.skip_turn = True
                self.current_turn = "player"
            else:
                self.current_turn = "computer"

            # If the player just discarded their last card, round ends
            if not self.player_hand:
                self.end_round("player")

    def computer_turn(self):
        # Simple logic: draw then discard a random card
        self.draw_card("computer")
        if self.computer_hand:
            idx = random.randint(0, len(self.computer_hand) - 1)
            card = self.computer_hand.pop(idx)
            self.discard_pile.append(card)
            if not self.computer_hand:
                self.end_round("computer")

        self.current_turn = "player"

    def end_round(self, winner):
        # Winner advances phase
        if winner == "player":
            self.player_phase += 1
        else:
            self.computer_phase += 1

        self.round += 1
        self.start_new_hand()

    # ------------------------------
    # Phase Submission (Sets + Runs)
    # ------------------------------

    def add_to_phase_attempt(self, card_index):
        if 0 <= card_index < len(self.player_hand):
            card = self.player_hand.pop(card_index)
            self.phase_submission_box.append(card)

    def remove_from_phase_attempt(self, card_index):
        if 0 <= card_index < len(self.phase_submission_box):
            card = self.phase_submission_box.pop(card_index)
            self.player_hand.append(card)

    def check_phase_attempt(self):
        """
        Returns True if the cards in self.phase_submission_box satisfy
        the player's current phase (e.g. Phase 1 => 2 sets of 3,
        Phase 2 => 1 set of 3 and 1 run of 4, etc.).
        
        For demonstration, this method only checks:
          - Phase 1 (2 sets of 3)
          - Phase 2 (1 set of 3 + 1 run of 4)
          - Phase 3 (1 set of 4 + 1 run of 4)
          - Phase 4-6 (Run-only phases with required len of 7,8,9)
        """
        phase_goal = self.PHASES[self.player_phase]
        combos = self.parse_phase_combination(self.phase_submission_box, phase_goal)
        return combos is not None

    def submit_phase(self):
        """
        If the submission box satisfies the player's current phase,
        store these combos in played_phases["player"] and clear the submission box.
        """
        phase_goal = self.PHASES[self.player_phase]
        combos = self.parse_phase_combination(self.phase_submission_box, phase_goal)
        if combos is not None:
            # Successful
            self.played_phases["player"].extend(combos)
            self.phase_submission_box.clear()
            self.phase_submitted = True

    # ------------------------------
    # Parsing a Combination of Cards
    # into the required sets/runs
    # ------------------------------
    def parse_phase_combination(self, cards, phase_goal):
        """
        Attempt to partition 'cards' into combos that satisfy 'phase_goal'.
        If successful, return a list of combos (each combo is a dict).
        If not, return None.
        
        Currently only handles:
          - Phase 1: 2 sets of 3
          - Phase 2: 1 set of 3 + 1 run of 4
        """
        sets_needed = phase_goal.get("sets", 0)
        set_size = phase_goal.get("set_size", 0)
        run_length = phase_goal.get("run", 0)


        # Convert to a list so we can manipulate
        card_list = list(cards)

        # If Phase 1: 2 sets of 3
        if sets_needed == 2 and set_size == 3 and run_length == 0:
            combos = self._try_form_two_sets_of_three(card_list)
            return combos

        # If Phase 2: 1 set of 3 + 1 run of 4
        if sets_needed == 1 and set_size == 3 and run_length == 4:
            combos = self._try_form_one_set_and_one_run(card_list)
            return combos

        # If Phase 3: 1 set of 4 and 1 run of 4
        if sets_needed == 1 and set_size == 4 and run_length == 4:
            combos = self._try_form_one_set_and_one_run3(card_list)
            return combos

        # If Phase 4-6: no set requirement only a run
        if sets_needed == 0 and run_length > 0:
            success, used_run, run_cards_sorted = self._can_form_run(card_list, run_length)
            if success:
                return [{"type": "run", "cards": run_cards_sorted}]
            else:
                return None
                
        # Otherwise, not implemented yet
        return None

    def _try_form_two_sets_of_three(self, card_list):
        """
        Try to form exactly 2 sets of 3 from the card_list.
        Return a list of combos if successful, else None.
        """
        if len(card_list) < 6:
            return None

        # First set
        success1, used1, set_num1 = self._can_form_set(card_list, 3)
        if not success1:
            return None
        # Remove used1 from card_list
        leftover1 = [c for i, c in enumerate(card_list) if i not in used1]

        # Second set
        success2, used2, set_num2 = self._can_form_set(leftover1, 3)
        if not success2:
            return None

        # Build combos
        set_cards_1 = [card_list[i] for i in used1]
        set_cards_2 = []
        # used2 are indices into leftover1, so we need to map them back
        # leftover1 was the subset, we must figure out which indices in leftover1
        # correspond to which indices in card_list
        leftover_map = []
        used_in_card_list = set(used1)
        for i, c in enumerate(card_list):
            if i not in used_in_card_list:
                leftover_map.append(i)  # track original indices

        real_indices_2 = [leftover_map[i] for i in used2]
        set_cards_2 = [card_list[i] for i in real_indices_2]

        combos = [
            {"type": "set", "cards": set_cards_1, "number": set_num1},
            {"type": "set", "cards": set_cards_2, "number": set_num2},
        ]
        return combos

    def _try_form_one_set_and_one_run(self, card_list):
        """
        Try to form exactly 1 set of 3 and 1 run of 4 from card_list.
        Return a list of combos if successful, else None.
        """
        if len(card_list) < 7:
            return None

        # Attempt set first, then run
        success_set, used_set, set_num = self._can_form_set(card_list, 3)
        if success_set:
            leftover1 = [c for i, c in enumerate(card_list) if i not in used_set]
            success_run, used_run, run_cards_sorted = self._can_form_run(leftover1, 4)
            if success_run:
                # Build combos
                set_cards = [card_list[i] for i in used_set]
                # used_run are indices into leftover1
                leftover_map = []
                used_in_card_list = set(used_set)
                for i, c in enumerate(card_list):
                    if i not in used_in_card_list:
                        leftover_map.append(i)
                real_indices_run = [leftover_map[i] for i in used_run]
                run_cards = [card_list[i] for i in real_indices_run]

                combos = [
                    {"type": "set", "cards": set_cards, "number": set_num},
                    {"type": "run", "cards": run_cards_sorted},
                ]
                return combos

        # Try run first, then set
        success_run, used_run, run_cards_sorted = self._can_form_run(card_list, 4)
        if success_run:
            leftover2 = [c for i, c in enumerate(card_list) if i not in used_run]
            success_set, used_set, set_num = self._can_form_set(leftover2, 3)
            if success_set:
                run_map = []
                used_in_card_list = set(used_run)
                for i, c in enumerate(card_list):
                    if i not in used_in_card_list:
                        run_map.append(i)
                real_indices_set = [run_map[i] for i in used_set]
                set_cards = [card_list[i] for i in real_indices_set]

                combos = [
                    {"type": "run", "cards": run_cards_sorted},
                    {"type": "set", "cards": set_cards, "number": set_num},
                ]
                return combos

        return None

    def _try_form_one_set_and_one_run3(self, card_list):
        """
        Try to form exactly 1 set of 4 and 1 run of 4 from card_list.
        Return a list of combos if successful, else None.
        """
        if len(card_list) < 8:
            return None

        # Attempt set first, then run
        success_set, used_set, set_num = self._can_form_set(card_list, 4)
        if success_set:
            leftover1 = [c for i, c in enumerate(card_list) if i not in used_set]
            success_run, used_run, run_cards_sorted = self._can_form_run(leftover1, 4)
            if success_run:
                # Build combos
                set_cards = [card_list[i] for i in used_set]
                # used_run are indices into leftover1
                leftover_map = []
                used_in_card_list = set(used_set)
                for i, c in enumerate(card_list):
                    if i not in used_in_card_list:
                        leftover_map.append(i)
                real_indices_run = [leftover_map[i] for i in used_run]
                run_cards = [card_list[i] for i in real_indices_run]

                combos = [
                    {"type": "set", "cards": set_cards, "number": set_num},
                    {"type": "run", "cards": run_cards_sorted},
                ]
                return combos

        # Try run first, then set
        success_run, used_run, run_cards_sorted = self._can_form_run(card_list, 4)
        if success_run:
            leftover2 = [c for i, c in enumerate(card_list) if i not in used_run]
            success_set, used_set, set_num = self._can_form_set(leftover2, 4)
            if success_set:
                run_map = []
                used_in_card_list = set(used_run)
                for i, c in enumerate(card_list):
                    if i not in used_in_card_list:
                        run_map.append(i)
                real_indices_set = [run_map[i] for i in used_set]
                set_cards = [card_list[i] for i in real_indices_set]

                combos = [
                    {"type": "run", "cards": run_cards_sorted},
                    {"type": "set", "cards": set_cards, "number": set_num},
                ]
                return combos

        return None

    # ------------------------------
    # Helper: _can_form_set
    # ------------------------------
    def _can_form_set(self, cards_list, size):
        """
        Tries to extract exactly one set of `size` from cards_list.
        Returns (True, used_indices, set_number) if success, else (False, [], None).
        A 'set' is all the same number, plus any wilds as needed.
        """
        from collections import defaultdict

        # Indices of wilds
        wild_indices = []
        normal_map = defaultdict(list)  # number -> list of indices

        for i, c in enumerate(cards_list):
            if c.is_wild():
                wild_indices.append(i)
            else:
                normal_map[c.number].append(i)

        # Check each number to see if we can form a set
        for number, idx_list in normal_map.items():
            count = len(idx_list)
            if count >= size:
                # We have enough real cards
                used = idx_list[:size]
                return True, used, number
            else:
                needed = size - count
                if needed <= len(wild_indices):
                    # We can fill with wilds
                    used = idx_list[:]  # all real cards
                    used += wild_indices[:needed]
                    return True, used, number

        return False, [], None

    # ------------------------------
    # Helper: _can_form_run
    # ------------------------------
    def _can_form_run(self, cards_list, length):
        """
        Tries to form a consecutive run of `length` using wilds.
        Returns (True, used_indices, sorted_cards_for_run) if success,
        else (False, [], []).
        
        Example: run of 4 could be [4,5,Wild,7].
        Color is irrelevant, only numeric sequence matters.
        """
        import itertools

        if len(cards_list) < length:
            return False, [], []

        indices = list(range(len(cards_list)))
        # We'll try all combinations of exactly `length` cards
        for combo in itertools.combinations(indices, length):
            combo_cards = [cards_list[i] for i in combo]
            # Count how many are wild
            wild_count = sum(1 for c in combo_cards if c.is_wild())
            # Extract real numbers
            real_nums = sorted([c.number for c in combo_cards if not c.is_wild()])

            if not real_nums:
                # All wild? Then we can form a run of anything, but let's assume
                # we need at least 1 real number to anchor. (Up to you to define.)
                continue

            min_num = real_nums[0]
            max_num = real_nums[-1]
            needed_gaps = (max_num - min_num + 1) - len(real_nums)
            # E.g. real_nums=[4,5,7], min=4, max=7 => gap=4 => need 1 to fill '6'

            # If the total range is bigger than we can fill with wilds, fail
            if (max_num - min_num + 1) > length:
                continue

            # If we can fill the gaps with the available wilds
            if needed_gaps <= wild_count and (max_num - min_num + 1) <= (length + wild_count):
                # Sort the actual cards for returning
                used_indices = list(combo)
                # Reconstruct the final run in ascending order
                # For display, you might want the real numbers in ascending order
                run_sorted = sorted(combo_cards, key=lambda c: (c.is_wild(), c.number if not c.is_wild() else 999))
                return True, used_indices, run_sorted

        return False, [], []

    # ------------------------------
    # Hitting Logic
    # ------------------------------
    def hit_existing_phase(self, card_index):
        """
        Add a single card from player_hand[card_index] to one of the combos
        in played_phases["player"], if it is valid to do so.
        Minimal example:
          - If combo is a set => same number or wild
          - If combo is a run => extend from left or right by 1 or wild
        """
        if 0 <= card_index < len(self.player_hand):
            card = self.player_hand[card_index]

            # Must have laid your phase first to have combos
            if not self.played_phases["player"]:
                return  # no combos to hit

            for combo in self.played_phases["player"]:
                if combo["type"] == "set":
                    # If the set is all number X (plus wilds), we can add this card
                    # if it is wild or matches X
                    set_number = self._get_set_number(combo["cards"])
                    if set_number is not None:
                        if card.is_wild() or (not card.is_wild() and card.number == set_number):
                            # Add to set
                            combo["cards"].append(card)
                            self.player_hand.pop(card_index)
                            return
                elif combo["type"] == "run":
                    # Minimal approach: check if we can place it at either end
                    # For example, if run is [6,7,8], we can add a 5 or 9 or a Wild
                    # For a robust approach, you'd handle wild insertion or big runs
                    run_cards = combo["cards"]
                    # Sort them by actual number (wilds last)
                    run_nums = sorted([c.number for c in run_cards if not c.is_wild()])
                    if not run_nums:
                        continue
                    low = min(run_nums)
                    high = max(run_nums)
                    # If card is wild, we can place it on either end
                    if card.is_wild():
                        run_cards.append(card)
                        self.player_hand.pop(card_index)
                        return
                    else:
                        # If card.number == low - 1 or high + 1
                        if card.number == low - 1 or card.number == high + 1:
                            run_cards.append(card)
                            self.player_hand.pop(card_index)
                            return

            # If we get here, we couldn't add the card to any combo
            return

    def _get_set_number(self, cards):
        """
        Given a list of cards forming a set, find the 'number' 
        ignoring wilds. Return None if ambiguous.
        """
        real_numbers = [c.number for c in cards if not c.is_wild()]
        if not real_numbers:
            return None
        # If the set is valid, they should all be the same real number
        first = real_numbers[0]
        for num in real_numbers:
            if num != first:
                return None
        return first
