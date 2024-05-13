import os
os.system('pip3 install -r requirements.txt')

import chess
import chess.svg
import chess.engine
import random
import time
import uuid
import re
import requests
import zipfile
import platform
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

load_dotenv()


def get_piece_from_class(piece_class):
    try:
        piece_color = chess.BLACK if piece_class.startswith('b') else chess.WHITE
        piece_type = {
            'p': chess.PAWN,
            'r': chess.ROOK,
            'n': chess.KNIGHT,
            'b': chess.BISHOP,
            'q': chess.QUEEN,
            'k': chess.KING
        }[piece_class[1]]
        return chess.Piece(piece_type, piece_color)
    except Exception as e:
        print("Error, code 1:", e)

def get_board_from_web(driver):
    try:
        board_element = driver.find_element("css selector", 'div.board-layout-chessboard')
        html_structure = board_element.get_attribute('outerHTML')
        return html_structure    
    except Exception as e:
        print("Error, code 2:", e)
def get_user_data_dir():
    base_dir = os.path.join(os.getcwd(), "user_data")
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    user_data_file = os.path.join(base_dir, "user_data_dir.txt")
    if os.path.exists(user_data_file):
        with open(user_data_file, "r") as file:
            user_dir = file.read().strip()
    else:
        user_dir = create_user_data_dir()
        with open(user_data_file, "w") as file:
            file.write(user_dir)
    return user_dir

def create_user_data_dir():
    user_dir = os.path.join(os.getcwd(), "user_data", str(uuid.uuid4()))
    os.mkdir(user_dir)
    return user_dir


level = os.getenv("level")
stockfish_path = os.getenv("stockfish_path")
profile_path = get_user_data_dir()
max_delay = 1

if level.isdigit() == False and level == "stockfish":
    level = 0
elif level.isdigit() == True:
    level = int(level)
    if level == 1:
        level = 0.5
        max_delay = 17
    elif level == 2:
        level = 0.25
        max_delay = 14
    elif level == 3:
        level = 0.1
        max_delay = 11
    elif level == 4:
        level = 0.01
        max_delay = 5
elif level.isdigit() == False and level == "random":
    level = random.randint(0.01, 0.5)
else:
    raise Exception("Level must be either a number between 1 (worst) and 4 (best, but still makes mistakes), 'stockfish' (raw engine, BE CAREFUL WITH THIS) or 'random'.")

def get_best_move(board):
    try:
        pooe = random.random()
        if pooe < level:
            print("Random move. " + str(pooe) + " < " + str(level) + ".")
            legal_moves = [move for move in board.legal_moves]
            random_move = random.choice(legal_moves)
            return random_move

        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        result = engine.play(board, chess.engine.Limit(time=0.1))
        engine.quit()
        return result.move
    except Exception as e:
        print("Error, code 3:", e)

def announce_move(move):
    pass

def make_move_on_board(driver, move, board, team, f):
    try:
        global max_delay
        letterlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

        source_square = move[:2]
        dest_square = move[2:]

        source_digit = letterlist.index(source_square[0]) + 1
        source_square_coord = str(source_digit) + source_square[1]

        dest_digit = letterlist.index(dest_square[0]) + 1
        dest_square_coord = str(dest_digit) + dest_square[1]

        piece = board.piece_at(chess.SQUARE_NAMES.index(source_square))
        piece_type = piece.symbol()
        piece_color = "w" if piece.color == chess.WHITE else 'b'
        piece_class = f'{piece_color}{piece_type}'
        piece_class = piece_class.lower()

        piece_selector = f'div.piece.{piece_class}.square-{source_square_coord}'
        dest_square_hint_selector = f'div.hint.square-{dest_square_coord}'

        capture_hint_selector = f'div.capture-hint.square-{dest_square_coord}'

        print("Piece Selector:", piece_selector)
        print("Dest Square Hint Selector:", dest_square_hint_selector)

        try:
            piece_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, piece_selector))
            )
            if f != True:
                delay = random.randint(1, max_delay)
            else:
                delay = random.randint(1, 3)
            for i in range(delay):
                print(f"Waiting for {delay - i} seconds... \n")
                time.sleep(1)
            piece_element.click()

            time.sleep(0.2)
            if driver.find_elements(By.CSS_SELECTOR, dest_square_hint_selector):
                dest_square_hint_selector = dest_square_hint_selector
                dest_square_hint_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, dest_square_hint_selector))
                )
            else:
                dest_square_hint_selector = capture_hint_selector
                dest_square_hint_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, dest_square_hint_selector))
                )

            time.sleep(random.random() * 0.5)

            actions = ActionChains(driver)
            actions.move_to_element(dest_square_hint_element).click().perform()

            if len(move) == 5 and move[4] in ['q', 'r', 'b', 'n']:
                promotion_window_top_selector = 'div.promotion-window.top'
                promotion_piece_selector = f'div.promotion-piece.{team+move[4].lower()}'

                promotion_window_top = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, promotion_window_top_selector))
                )

                promotion_piece_element = promotion_window_top.find_element(
                    By.CSS_SELECTOR, promotion_piece_selector
                )

                promotion_piece_element.click()
        except Exception as e:
            print("Error, code 4:", e)
    except Exception as e:
        print("Error, code 5:", e)

def calculate_and_announce_move(driver, board, team, fmove):
    try:
        global last_board
        print("Calculating move...")
        html_structure = get_board_from_web(driver)
        soup = BeautifulSoup(html_structure, 'html.parser')
        board = chess.Board()
        board.clear()
        if team == "w":
            board.turn = chess.WHITE
        elif team == "b":
            board.turn = chess.BLACK

        for piece_div in soup.select('div.piece'):
            piece_class_match = re.search(r'([wb][prnbqk])', ' '.join(piece_div['class']))
            square_position_match = re.search(r'square-(\d{2})', ' '.join(piece_div['class']))

            if piece_class_match and square_position_match:
                piece_class = piece_class_match.group(1)
                square_position = square_position_match.group(1)
            else:
                continue

            letterlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            double_digit_square = square_position
            first_digit, second_digit = map(int, list(double_digit_square))

            letter = letterlist[first_digit - 1]
            number = second_digit
            algebraic_notation = letter + str(number)
            square_index = chess.SQUARE_NAMES.index(algebraic_notation)
            piece = get_piece_from_class(piece_class)
            board.set_piece_at(square_index, piece)

        best_move = get_best_move(board)
        announce_move(best_move.uci())
        print(best_move)

        best_move_str = str(best_move)

        make_move_on_board(driver, best_move_str, board, team, fmove)
        if team == "w":
            board.turn = chess.BLACK
        elif team == "b":
            board.turn = chess.WHITE
        last_board.clear()
        for piece_div in soup.select('div.piece'):
            piece_class_match = re.search(r'([wb][prnbqk])', ' '.join(piece_div['class']))
            square_position_match = re.search(r'square-(\d{2})', ' '.join(piece_div['class']))

            if piece_class_match and square_position_match:
                piece_class = piece_class_match.group(1)
                square_position = square_position_match.group(1)
            else:
                continue

            letterlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            double_digit_square = square_position
            first_digit, second_digit = map(int, list(double_digit_square))

            letter = letterlist[first_digit - 1]
            number = second_digit
            algebraic_notation = letter + str(number)
            square_index = chess.SQUARE_NAMES.index(algebraic_notation)
            piece = get_piece_from_class(piece_class)
            last_board.set_piece_at(square_index, piece)
    except Exception as e:
        print("Error, code 6:", e)
        print("Could not calculate move. Check selectors and HTML structure.")
    except KeyboardInterrupt:
        driver.quit()
        exit()

def has_board_changed_and_which_color(last_board, current_board, team):
    try:
        color = None
        if team == "w":
            team = chess.WHITE
        elif team == "b":
            team = chess.BLACK
        for square in chess.SQUARES:
            if last_board.piece_at(square) != current_board.piece_at(square):
                piece = current_board.piece_at(square)
                if piece is not None:
                    color = piece.color
                    if team == chess.WHITE and color == chess.BLACK: 
                        break
                    elif team == chess.BLACK and color == chess.WHITE: 
                        break
        print("Color moved:", color)

        return str(last_board) != str(current_board), color
    except Exception as e:
        print("Error, code 7:", e)

def main():

    global driver 
    options = webdriver.EdgeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    driver = webdriver.Edge(options=options)
    driver.get('https://www.chess.com/play/online')

    global last_board
    last_board = chess.Board()
    first_move = True
    while True:
        try:
            time.sleep(0.1)
            html_structure = get_board_from_web(driver)
            soup = BeautifulSoup(html_structure, 'html.parser')
            coordinate_light_element = soup.find('text', {'y': '3.5', 'class': 'coordinate-light'})
            
            if coordinate_light_element and coordinate_light_element.text == '8':
                team_prompt = "w" 
            else:
                team_prompt = "b" 

            current_board = chess.Board()
            current_board.clear()
        
            for piece_div in soup.select('div.piece'):
                piece_class_match = re.search(r'([wb][prnbqk])', ' '.join(piece_div['class']))
                square_position_match = re.search(r'square-(\d{2})', ' '.join(piece_div['class']))

                if piece_class_match and square_position_match:
                    piece_class = piece_class_match.group(1)
                    square_position = square_position_match.group(1)
                else:
                    continue

                letterlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                double_digit_square = square_position
                first_digit, second_digit = map(int, list(double_digit_square))

                letter = letterlist[first_digit - 1]
                number = second_digit
                algebraic_notation = letter + str(number)
                square_index = chess.SQUARE_NAMES.index(algebraic_notation)
                piece = get_piece_from_class(piece_class)
                current_board.set_piece_at(square_index, piece)
            if current_board != current_board.is_game_over():
                if current_board == chess.Board() and team_prompt == "w":
                    first_move = True
                changed, color_moved = has_board_changed_and_which_color(last_board=last_board, current_board=current_board, team=team_prompt)
                if team_prompt == "w":
                    team = team_prompt
                    if first_move:
                        print("Team detected:", team)
                        first_move = False
                        calculate_and_announce_move(driver, current_board, team, True)
                        last_board.clear()
                        for piece_div in soup.select('div.piece'):
                            piece_class_match = re.search(r'([wb][prnbqk])', ' '.join(piece_div['class']))
                            square_position_match = re.search(r'square-(\d{2})', ' '.join(piece_div['class']))

                            if piece_class_match and square_position_match:
                                piece_class = piece_class_match.group(1)
                                square_position = square_position_match.group(1)
                            else:

                                continue

                            letterlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                            double_digit_square = square_position
                            first_digit, second_digit = map(int, list(double_digit_square))

                            letter = letterlist[first_digit - 1]
                            number = second_digit
                            algebraic_notation = letter + str(number)
                            square_index = chess.SQUARE_NAMES.index(algebraic_notation)
                            piece = get_piece_from_class(piece_class)
                            last_board.set_piece_at(square_index, piece)
                    if changed == True and color_moved == False:
                        print("Team detected:", team)
                        print("Board has changed. Calculating move.")
                        calculate_and_announce_move(driver, current_board, team, False)
                        last_board.clear()
                        for piece_div in soup.select('div.piece'):
                            piece_class_match = re.search(r'([wb][prnbqk])', ' '.join(piece_div['class']))
                            square_position_match = re.search(r'square-(\d{2})', ' '.join(piece_div['class']))

                            if piece_class_match and square_position_match:
                                piece_class = piece_class_match.group(1)
                                square_position = square_position_match.group(1)
                            else:

                                continue

                            letterlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                            double_digit_square = square_position
                            first_digit, second_digit = map(int, list(double_digit_square))

                            letter = letterlist[first_digit - 1]
                            number = second_digit
                            algebraic_notation = letter + str(number)
                            square_index = chess.SQUARE_NAMES.index(algebraic_notation)
                            piece = get_piece_from_class(piece_class)
                            last_board.set_piece_at(square_index, piece)
                elif team_prompt == "b":
                    team = team_prompt
                    if changed == True and color_moved == True:
                        print("Team detected:", team)
                        print("Board has changed. Calculating move.")
                        if first_move:
                            calculate_and_announce_move(driver, current_board, team, True)
                        else:
                            calculate_and_announce_move(driver, current_board, team, False)
                        last_board.clear()
                        for piece_div in soup.select('div.piece'):
                            piece_class_match = re.search(r'([wb][prnbqk])', ' '.join(piece_div['class']))
                            square_position_match = re.search(r'square-(\d{2})', ' '.join(piece_div['class']))

                            if piece_class_match and square_position_match:
                                piece_class = piece_class_match.group(1)
                                square_position = square_position_match.group(1)
                            else:

                                continue

                            letterlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                            double_digit_square = square_position
                            first_digit, second_digit = map(int, list(double_digit_square))

                            letter = letterlist[first_digit - 1]
                            number = second_digit
                            algebraic_notation = letter + str(number)
                            square_index = chess.SQUARE_NAMES.index(algebraic_notation)
                            piece = get_piece_from_class(piece_class)
                            last_board.set_piece_at(square_index, piece)
            else:
                print("Game over. Exiting...")
                exit()
        except Exception as e:
            print("Error, code 8:", e)
        
if __name__ == "__main__":
    main()
