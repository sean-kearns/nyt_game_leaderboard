from django.db import models
from django.conf import settings
from users.models import Profile, User

# Create your models here.

class Game(models.Model):
    name = models.CharField(max_length = 100)

    def __str__(self):
        return self.name

class ConnectionsScore(models.Model):
    
    #Sample Connections text output:
    """
    Connections 
    Puzzle #255
    🟨🟩🟪🟨
    🟨🟨🟨🟨
    🟪🟩🟩🟦
    🟪🟩🟩🟩
    🟩🟩🟪🟩

    Connections 
    Puzzle #255
    🟨🟨🟨🟨
    🟩🟪🟩🟩
    🟩🟪🟩🟩
    🟩🟩🟪🟩
    🟩🟩🟩🟩
    🟪🟪🟪🟪
    🟦🟦🟦🟦
    """
    raw_score_details = models.TextField()
    game = 'Test Game'
    player_name = models.CharField(max_length = 100)
    puzzle_number = models.IntegerField(null = True, blank = True)
    score_details = models.TextField()
    score_value = models.IntegerField(null = True, blank = True)
    date = models.DateTimeField(auto_now_add = True)
    score_comment = models.CharField(max_length = 10, default = '', blank = True)

    def save(self, *args, **kwargs):
        self.score_details = self.parse_raw_score_details(self.raw_score_details)
        super(ConnectionsScore, self).save(*args, **kwargs)

    def parse_raw_score_details(self, raw_details):
        #Parse based on NYT Connections output text
        square_data = [i.strip() for i in raw_details.strip().split('\n')] #s will be a list ['Connections', 'Puzzle #xxx', {square row 1}, {square row 2}, etc...]
        sqaures = square_data[2:]
        
        self.score_value = self.calculate_score(sqaures)
        
        self.puzzle_number = int(square_data[1].split('#')[1]) #Isolates the puzzle number from the game data

        square_string = '\n'.join(square_data[2:])
        return square_string

    def calculate_score(self, puzzle_output):
        # Define difficulty weights and the correct order of colors (hardest to easiest)
        difficulty_weights = {'🟪': 4, '🟦': 3, '🟩': 2, '🟨': 1}
        correct_order = ['🟪', '🟦', '🟩', '🟨']
        
        # Base score and penalties
        base_score = 100
        order_penalty = 1  # For each deviation from the correct order in the first four guesses
        extra_guess_penalty = 10  # For each guess beyond the first four
        incorrect_final_penalty = 30  # Significant penalty if the final guess is incorrect
        
        # Initialize score
        score = base_score
        correct_guesses = 0
        
        # Check first four guesses for correctness and order
        for i, row in enumerate(puzzle_output[:4]):
            if len(set(row)) == 1:  # Row is correctly solved
                correct_guesses += 1
                # Check if the row is in the correct order of difficulty
                if row[0] != correct_order[i]:
                    score -= order_penalty
            else:
                break  # Stop checking if any of the first four rows is incorrect
        
        # Apply penalties for extra guesses if the puzzle was solved in more than four guesses
        if len(puzzle_output) > 4:
            # Ensure the puzzle was actually solved
            if all(len(set(row)) == 1 for row in puzzle_output[-4:]):
                score -= extra_guess_penalty * (len(puzzle_output) - 4)
            else:
                # Apply a larger penalty if the puzzle wasn't solved correctly even in extra guesses
                score -= extra_guess_penalty * len(puzzle_output)
        
        # Apply a significant penalty if the puzzle was not solved correctly (the last guess is incorrect)
        if len(set(puzzle_output[-1])) != 1:
            score -= incorrect_final_penalty
        
        # Ensure score does not exceed base score or fall below 0
        score = min(score, base_score)
        score = max(0, score)
        
        return score

    ##this function takes in a puzzle and returns 1 if successful and 0 if not 
    def is_successful_puzzle(self):
        print(self.score_details)
        square_data = [i.strip() for i in self.score_details.strip().split('\n')] #s will be a list ['Connections', 'Puzzle #xxx', {square row 1}, {square row 2}, etc...]

        #a score needs all the right color combos for it to be correct 
        #this takes all perfect rows and subtracts matching rows 
        #leftovers should have all elements removed and return 1
        need_list = ['🟪🟪🟪🟪', '🟦🟦🟦🟦', '🟩🟩🟩🟩', '🟨🟨🟨🟨']
        leftovers = set(need_list) - set(square_data)
        if len(leftovers) > 0:
            return 0
        else:
            return 1
    
    def __str__(self):
        return f"{self.player_name} - {self.puzzle_number} - Puzzle #{self.puzzle_number}"

