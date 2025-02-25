import random
import collections

COLORS = ["Red", "Blue", "Green", "Yellow"]
NUMBERS = list(range(1, 13))
WILD_COUNT = 8
SKIP_COUNT = 4

PHASES = [
    {"sets": 2, "set_size": 3},  # Phase 1: Two sets of three
    {"sets": 1, "set_size": 3, "run": 4},
    {"sets": 1, "set_size": 4, "run": 4},
    {"run": 7},
    {"run": 8},
    {"run": 9},
    {"sets": 2, "set_size": 4},
    {"color": 7},
    {"sets": 1, "set_size": 5, "set_2": 2},
    {"sets": 1, "set_size": 5, "set_2": 3},
]

class Card:
    def __init__(self, color, number):
        self.color = color
        self.number = number

    def is_wild(self):
        return self.number == "Wild"

    def is_skip(self):
        return self.number == "Skip"

def create_deck():
    deck = [Card(color, num) for color in COLORS for num in NUMBERS for _ in range(2)]
    deck += [Card(None, "Wild")] * WILD_COUNT
    deck += [Card(None, "Skip")] * SKIP_COUNT
    random.shuffle(deck)
    return deck

class Game:
    PHASES = PHASES

    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.deck = create_deck()
        self.discard_pile = [self.deck.pop()]
        self.player_hand = [self.deck.pop() for _ in range(10)]
        self.computer_hand = [self.deck.pop() for _ in range(10)]
        self.player_phase = 0
        self.computer_phase = 0
        self.current_turn = "player"
        self.has_drawn = False
        self.skip_turn = False  
        self.played_phases = {"player": [], "computer": []}
        self.phase_submission_box = []  
        self.selected_card_index = None
        self.phase_submitted = False  # New flag: phase has been submitted this turn

    def draw_card(self, player, from_discard=False):
        if self.phase_submitted:
            # Once a phase is submitted, no further drawing is allowed.
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

            if card.is_skip():
                self.skip_turn = True  
                self.current_turn = "player"
            else:
                self.current_turn = "computer"

            if not self.player_hand:
                self.end_round("player")

    def add_to_phase_attempt(self, card_index):
        if 0 <= card_index < len(self.player_hand):
            card = self.player_hand.pop(card_index)
            self.phase_submission_box.append(card)

    def remove_from_phase_attempt(self, card_index):
        if 0 <= card_index < len(self.phase_submission_box):
            card = self.phase_submission_box.pop(card_index)
            self.player_hand.append(card)

    def check_phase_attempt(self):
        phase_goal = PHASES[self.player_phase]
        number_counts = collections.Counter(c.number for c in self.phase_submission_box if not c.is_wild())
        wild_count = sum(1 for c in self.phase_submission_box if c.is_wild())

        sets_needed = phase_goal.get("sets", 0)
        set_size = phase_goal.get("set_size", 0)

        formed_sets = 0
        for num, count in sorted(number_counts.items(), key=lambda x: -x[1]):
            if count >= set_size:
                formed_sets += 1
            elif count + wild_count >= set_size:
                wild_count -= (set_size - count)
                formed_sets += 1

            if formed_sets >= sets_needed:
                return True
        return False

    def submit_phase(self):
        if self.check_phase_attempt():
            self.played_phases["player"].extend(self.phase_submission_box)
            self.phase_submission_box.clear()
            self.phase_submitted = True  # Mark phase as submitted so no further drawing is allowed

    def hit_existing_phase(self, card_index):
        if 0 <= card_index < len(self.player_hand):
            card = self.player_hand.pop(card_index)
            self.played_phases["player"].append(card)

    def computer_turn(self):
        # Simple computer logic: draw a card and discard a random card.
        self.draw_card("computer")
        if self.computer_hand:
            card_index = random.randint(0, len(self.computer_hand) - 1)
            card = self.computer_hand.pop(card_index)
            self.discard_pile.append(card)
        self.current_turn = "player"

    def end_round(self, winner):
        if winner == "player":
            self.player_phase += 1
        else:
            self.computer_phase += 1
        self.reset_game()
