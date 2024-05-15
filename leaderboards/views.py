from django.shortcuts import render, redirect, get_object_or_404, reverse
# from .forms import ConnectionsScoreForm, ConnectionsScoreCommentForm
from .forms import ConnectionsScoreForm
from .models import ConnectionsScore
from users.models import Profile, User
from users.views import user_profile_view
from django.contrib import messages
from django.urls import reverse

from django.contrib import messages

# Create your views here.
def leaderboard_view(request):
    leaderboard_scores = ConnectionsScore.objects.order_by('puzzle_number', 'score_value').reverse()


    context = {'leaderboard_scores': leaderboard_scores}
    return render(request, 'leaderboards/global_leaderboard.html', context)

def submit_score(request):
    if request.method == "POST":
        form = ConnectionsScoreForm(request.POST, player_name=request.user.username)
        #comment_form = ConnectionsScoreCommentForm(request.POST, player_name=request.user.username)
        if form.is_valid():
            score_instance = form.save()
            # if comment_form.is_valid():
                # If comment form is valid, save the comment associated with the score
                # comment_instance = comment_form.save(commit=False)
                # comment_instance.score = score_instance
                # comment_instance.save()
            return redirect('leaderboards:leaderboard')  # Redirect to leaderboard page
        else:
            pass
            # Form(s) are not valid, display errors for both forms
            # print("Forms are not valid:", form.errors, comment_form.errors)
    else:
        form = ConnectionsScoreForm()
        # comment_form = ConnectionsScoreCommentForm()
    
    return render(request, 'leaderboards/submit_score.html', {'form': form})
    # render(request, 'leaderboards/submit_score.html', {'form': form, 'comment_form': comment_form})

# #Get Score Comment - ACTUALLY JUST NEEDED TO BUILD THIS INTO SUBMIT_SCORE
# def submit_score_comment(request):
#     if request.method == "POST":
#         form = ConnectionsScoreCommentForm(request.POST)

#         if form.is_valid():
#             return redirect('leaderboards: leaderboard')
#     else:
#         form = ConnectionsScoreCommentForm()
    
#     return render(request, 'leaderboards/submit_score.html', {'comment_form': form})
    
    
# Create your views here.
def leaderboard_view_following(request, username):

    print('Switching view')
    #if user is not authenticated, return to leaderboard view with a message saying you must be logged in 
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to see following leaderboard.")
        print('Not Authenticated')
        return redirect(reverse('leaderboards:leaderboard'))
    if request.user.username == 'PLACEHOLDER':
        messages.error(request, "You must be logged in to see following leaderboard.")
        print('Placeholder name')
        return redirect(reverse('leaderboards:leaderboard'))

    #gets all leaderboard scores 
    leaderboard_scores = ConnectionsScore.objects.order_by('puzzle_number', 'score_value').reverse()
    
    #obtain the instance of the profile and user based on the username on the page 
    user_profile = get_object_or_404(Profile, user__username=username)
    user = get_object_or_404(User, username=username)

    # Get the list of friends' profiles from the profile object method called get_friends_profiles_following/followers 
    friends_profiles_following = user_profile.get_friends_profiles_following()
    friends_users_following = []
    for friend_profile in friends_profiles_following:
        friends_users_following.append(friend_profile.user.username)
    
    
    print(f'users_following: {friends_users_following}')#['skearns', 'test123', 'test124']

    #added this code to return filtered scores 
    #this fixes the re-indexing issue of new scores 
    filtered_leaderboard_scores = []
    for score in leaderboard_scores:
        ##include scores of following players as well as their own score 
        if (score.player_name in friends_users_following or score.player_name == request.user.username): 
            filtered_leaderboard_scores.append(score)


    context = {'leaderboard_scores': filtered_leaderboard_scores,
                'user': user, 
                'friends_profiles_following': friends_users_following}
    return render(request, 'leaderboards/following_leaderboard.html', context)