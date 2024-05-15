from django import forms
from .models import Game, ConnectionsScore
import re

class ConnectionsScoreForm(forms.ModelForm):
    #Need to take player_name as an argument to the form, dynamically retrieved from POST request
    def __init__(self, *args, player_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_name = player_name  # Store the username
        #TODO: Checking/verifying username?

        # initial_content = "Paste in Your Score!\nConnections\nPuzzle #\n🟪🟪🟪🟪\n🟦🟦🟦🟦\n🟨🟨🟨🟨\n🟩🟩🟩🟩"
        # self.fields['raw_score_details'].initial = initial_content
        self.fields['raw_score_details'].widget.attrs.update({
            'class': 'form-control',
            'rows': 10,  # Adjust the number of rows as needed
            'cols': 8,
            # 'style': 'color: grey;',  # Style for the initial content
            'placeholder': "Paste in Your Score!\nConnections\nPuzzle #\n🟪🟪🟪🟪\n🟦🟦🟦🟦\n🟨🟨🟨🟨\n🟩🟩🟩🟩"
        })

        # initial_content = "Submit a one word comment on today's puzzle!"
        # self.fields['score_comment'].initial = initial_content
        self.fields['score_comment'].widget.attrs.update({
            'class': 'form-control',
            'rows': 1,  # Adjust the number of rows as needed
            'cols': 10,
            # 'style': 'color: grey;',  # Style for the initial content
            'placeholder': "Submit a one word commment on today's puzzle!"
        })

    def clean_raw_score_details(self):
        data = self.cleaned_data['raw_score_details']

        # Check Puzzle Number
        puzzle_number_match = re.search(r'Puzzle #(\d+)', data)
        if not puzzle_number_match:
            raise forms.ValidationError('Invalid Puzzle Number. Support for ConnectionsPlus Custom Puzzles coming soon')

        # Isolate the squares using the match's end position as the starting point
        square_data = data[puzzle_number_match.end():].strip() # 
        print("Debugging square_data:", repr(square_data))  # Continue to use repr() for visibility

        # Regex validation: accepts, \r \n and the square unicode characters
        #valid_square_regex = r'^\n*([\🟪\🟨\🟩\🟦]{4}(\r?\n)){1,7}$' #More strict pattern
        valid_square_regex = r'^[\r\n]*([\U0001F7EA\U0001F7E6\U0001F7E8\U0001F7E9\r\n]+)$'
        if not re.match(valid_square_regex, square_data):
            raise forms.ValidationError('Invalid puzzle format.')

        return data


    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.player_name = self.player_name  # Set the CharField to the username
        if commit:
            instance.save()
            self.save_m2m()  # Necessary if your model form has many-to-many fields
        return instance

    class Meta:
        model = ConnectionsScore
        fields = [
            'raw_score_details',
            'score_comment'
        ]
        widgets = {
            'raw_score_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'cols': 8}),
            'score_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'cols': 10, 'required': False})
        }

# class ConnectionsScoreCommentForm(forms.Form):
#     def __init__(self, *args, player_name=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.player_name = player_name  # Store the username
#         #TODO: Checking/verifying username?

#         initial_content = "Submit a one word comment on today's puzzle!"
#         self.fields['score_comment'].initial = initial_content
#         self.fields['score_comment'].widget.attrs.update({
#             'class': 'form-control',
#             'rows': 1,  # Adjust the number of rows as needed
#             'cols': 10,
#             'style': 'color: grey;',  # Style for the initial content
#         })

#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         instance.player_name = self.player_name  # Set the CharField to the username
#         if commit:
#             instance.save()
#             self.save_m2m()  # Necessary if your model form has many-to-many fields
#         return instance
    
#     class Meta:
#         model = ConnectionsScore
#         fields = [
#             'score_comment'
#         ]
#         widgets = {
#             'score_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'cols': 10})
#         }
#     score_comment = forms.CharField(label="Score Comment", max_length=10)