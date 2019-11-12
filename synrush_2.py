import requests
import platform
import os
import json
from time import sleep
import sys
from multiprocessing import Process, Value, Array, freeze_support
from pynput.keyboard import Key, Listener
import ctypes
from bs4 import BeautifulSoup
import socket
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Docstring
#     - This script is a game that aims to improve the short term memory of the player
#         - An internet connection is tested before the game proceeds
#         - It gives the user a list of words to memorize, generated from a web scraping session 
#         - The game starts of with 60 seconds
#         - The user must input correctly typed and spelled words in the list, maximizing a score at the end of the game
#         - The user is penalized for taking hints on a point basis, but rewarded for an increasing number of correctly recalled words
#         - The user can choose to pause, quit or recieve a hint during the game
#         - Once the game is finished, the players name and score is logged on an online database
    
#     - Critical functionality,
#         - 13 methods were defined to streamline the process of generating the game environment.
#             - A multiprocessing to track game time whilst accepting user input simultaneously
#             - Authentication to Google Sheets to record game performance

# Known bugs
#     - check_internet() connection may timeout
#     - Security of google sheets authentication questionable

# Further implementations
#     - Allowing the user to input name and choose difficulty in the beggining of the game
#     - Sort leaderboard by score
#     - Find a more secure database
#     - Figure out how to produce an cross platform executable



# "Global" variable initialization
get_definition = True
get_synonyms = True
current_word = "incredible"
current_definition = ""
os_type = ""
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# Game header
header = f"""




\t   _____             ____             __  
\t  / ___/__  ______  / __ \__  _______/ /_ 
\t  \__ \/ / / / __ \/ /_/ / / / / ___/ __ \\
\t ___/ / /_/ / / / / _, _/ /_/ (__  ) / / /
\t/____/\__, /_/ /_/_/ |_|\__,_/____/_/ /_/ 
\t     /____/                               

"""

def check_internet():
    # https://stackoverflow.com/questions/28752174/checking-internet-connection-with-python
    timeout = 10

    try:
        slow_print("\n\n\tChecking internet connection before 10s timeout...", 0.01)
        socket.setdefaulttimeout(timeout)
        host = socket.gethostbyname("www.google.com")
        s = socket.create_connection((host, 80), 2)
        s.close()
        slow_print("\n\n\tOK!", 0.03)
        sleep(1)
        return True

    except:
        slow_print("\n\n\tInternet connection not detected. Please establish a connection before proceeding!\n\n", 0.03)
        return False

def get_leaderboard(scope):
    try:
        # creds = ServiceAccountCredentials.from_json(json_data)
        creds = ServiceAccountCredentials.from_json_keyfile_name('hultds5301-bedb91014e1e.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open('ds5301').sheet1
        return sheet
    except:
        return False

def update_leaderboard(sheet, username, score):
    sheet = get_leaderboard(scope)
    row = [username, score]
    index = len(sheet.get_all_values()) + 1
    sheet.insert_row(row, index)

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def slow_print(disp_text, speed):

    # Credit: https://gist.github.com/Y4suyuki/6805818
    for i in range(len(disp_text)):
        sleep(speed)
        sys.stdout.write(disp_text[i % len(disp_text)])
        sys.stdout.flush()

    return ""

def intro(header):
    clear_screen()
    introduction = f'''

    {header}
    
\tA game that improves your short term memory!

\tHere is how it works,
\t\t1. I'll show you a list of words TO MEMORIZE
\t\t3. The game will start, and you have to TYPE them back to me
\t\t4. You'll earn more points and time for correctly SPELT and FORMATTED words

\t\t...BUT you'll loose points for taking a hint!


\t**Your GOAL is to maximize your game points BEFORE THE TIME RUNS OUT!



\tThis is what the game screen will look like:

\t---------------------------
\tLess then 10s 
\tScore: 150

\tCorrect words: 17
\tRemaining words: 33
\tGame state: In Progress
\t---------------------------


\tYour FINAL score will be recorded on a leaderboard, for bragging rights ofcoarse.


\tAre you ready?

    '''
    slow_print(introduction, 0.03)
    input("\n\tPress any key to continue...")
    clear_screen()

def endGame(header, username, gamescore):
    global scope

    print(header)
    slow_print(f"""

    \tGame over!
        
        """, 0.02)
    
    try:
        sheet = get_leaderboard(scope)
        update_leaderboard(sheet, username.value, gamescore.value)
        slow_print("Leaderboard standings: \n\n", 0.03)
        for name, score in sheet.get_all_values():
            print("\t{}\t|\t{}".format(name, score))
    except:
        slow_print("\n\tThanks for playing Synrush!", 0.03)
        return ""
    
    slow_print("\n\n\tThanks for playing Synrush!", 0.03)
    
    _ = input("")
    return ""

def get_game_words(client, gameState):

    # scrape 50 words from jimpix.co.uk using BeautifullSoup
    random_easy_word_url = "https://jimpix.co.uk/generators/word-generator.asp"
    response = client.get(random_easy_word_url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    gameState.value = 1
    return ([i.text for i in soup.findAll("span", {"class": "words2"})], gameState)

def user_game_status(header, time, score, correct_words, total_words, gameState, gamePaused, getHint, user_name):
    # Update the game screen
    clear_screen()
    press_commands = f"""
\tPress commands:
\t1. Hint
\t2. Pause
\t3. End game

    """
    
    # Generate displayed based on whether game is paused or exited
    if gameState.value == 1:
        if gamePaused.value == 1:
            return header + f"""
\tGame paused!\n"""

        else:
            if (getHint.value == 1):
                return header + press_commands + f"""
\tLess then {time}s 
\tScore: {score.value}

\tCorrect words: {correct_words.value}
\tRemaining words: \n\n{" | ".join(total_words)}\n\n
\tGame state: {"In Progress" if getHint.value else "Game Over!"}"""
            else:
                return header + press_commands + f"""
\tLess then {time}s 
\tScore: {score.value}
    
\tCorrect words: {correct_words.value}
\tRemaining words: {total_words} \n
\tGame state: {"In Progress" if gameState.value else "Game Over!"}"""
    else:
        return endGame(header, user_name, score)

def check_time(time, gameState, user_choice, game_paused, user_name):

    # print("Timer started...")
    gameState.value == 1

     # While the user still has time on the clock, or has not paused the game
    while (gameState.value == 1):
        if (game_paused.value != 1):
            sleep(1)
            time.value -= 1

            if time.value < 1:
                gameState.value = 0
                print(user_game_status(header, None, None, None, None, gameState, game_paused, None, user_name))
                break

def test_words(time, game_state, user_choice, all_game_words, game_paused, g_score, g_hint, correct_words, user_name):

    print(user_game_status(header, time.value, g_score, correct_words, len(all_game_words), game_state, game_paused, g_hint, user_name))

    # End the game once they've correctly entered all words
    if correct_words.value > (len(all_game_words) + correct_words.value):
        game_state.value = 0
        slow_print("\n\n\tNice work {}! You've correctly entered every word in a {} item list.".format(user_name.value, (len(all_game_words) + correct_words.value)), 0.01)
        slow_print("\n\n\tTHAT is impressive!", 0.2)
        sleep(2)
        print(user_game_status(header, None, g_score, correct_words, all_game_words, game_state, game_paused, g_hint, user_name))
        return (game_state.value, correct_words.value)

    # Pause the thread for user 
    user_choice.value = input("\n\n\tEnter your word -> ")
    
    # Check user choice, and remove words that were correctly spelt on the list to stop them from being SHNEAAKY
    if user_choice.value in all_game_words:
        g_score.value += 10 + g_score.value
        correct_words.value += 1
        time.value += 8
        all_game_words.remove(user_choice.value)
        return (g_score.value, time.value, correct_words.value, all_game_words, user_choice.value)

    # Check if the user has paused the game
    if user_choice.value == "2":
        game_paused.value = 1
        return (game_paused.value, user_choice.value)

    # Allow the user to exit the game
    if user_choice.value == "3":
        game_state.value = 0
        print(user_game_status(header, None, g_score, correct_words, all_game_words, game_state, game_paused, g_hint, user_name))
        return (game_state.value, user_choice.value)

    # Allow the user to see the list, at the cost of loosing points
    if user_choice.value == "1":
        g_score.value -= 50
        time.value -= 8
        g_hint.value = 1
        print(user_game_status(header, time.value, g_score, correct_words, all_game_words, game_state, game_paused, g_hint, user_name))
        input("\n\n\t**Press any key to continue!")
        g_hint.value = 0
        return (g_score.value, g_hint.value, user_choice.value)

def main():

    # Initialize client object for web scraping, generate total 50 easy words for the game
    client = requests.Session()

    # Run multiprocess to track game clock, and tab button
    g_time = Value('i', 60)
    g_paused = Value('i', 0)
    g_state = Value('i', 1)
    g_score = Value('i', 100)
    g_hint = Value('i', 0)
    g_correct_words = Value('i', 0)
    u_choice = Value(ctypes.c_wchar_p, "")
    u_name = Value(ctypes.c_wchar_p, "")
    all_words = []

    # Initialize game
    #     - Get batch of 50 words, then randomly select one
    #     - Get initial list of synonyms
    #     - start the timer
    while len(all_words) < 1: 
        slow_print(f"""\n\n\n\tInitializing game...""", 0.01)
        all_words, g_state = get_game_words(client, g_state)
    
    u_name.value = input(slow_print("\n\n\tWhat's your name? ", 0.01))

    slow_print("\n\n\t{}, MEMORIZE these words:\n\n".format(u_name.value), 0.01)
    slow_print(" | ".join(all_words), 0.01)
    input("\n\n\t**Press any key to start the game!")
    p1 = Process(target=check_time, args=(g_time, g_state, u_choice, g_paused, u_name))
    p1.start()

    # Monitor various states of the game
    #     - Generate list of words and allow them to take as much time as they want learning the words...hehe
    #     - Evaluate the user decisions,
    #         - Decision to view words as long as they want, while the timer is running
    #         - Decision to end the game
    
    while (g_state.value == 1):
        # additional game state check required to account for timer multiprocess
        if (g_state.value != 0):
            if (g_paused.value != 1):
                test_words(g_time, g_state, u_choice, all_words, g_paused, g_score, g_hint, g_correct_words, u_name)
            else:
                clear_screen()
                print(user_game_status(header, None, None, None, None, g_state, g_paused, g_hint, u_name))
                if input("\n\tContinue game? (y/n) -> ").lower() == 'y':
                    g_paused.value = 0
        else:
            # Emergency break
            break

if __name__ == '__main__':
    freeze_support()
    if check_internet():
        clear_screen()
        intro(header)
        main()

# synonyms = getSynonyms("hatchback")
# print("Synonyms for word: {}", synonyms)
