from datetime import datetime
from pathlib import Path
import json
from typing import Union

import matplotlib.pyplot as plt
import pygame
import numpy as np
from skimage.transform import resize, rescale

# todo list:
#TODO: Add comments, like everywhere :p  (future me will thank current me : )
#TODO: unify all event/keypress checking into one function and just return a string (e.g., convert_event_to_action(keypress) --> 'up' or 'pause')

HEADER_HEIGHT_OFFSET = 50  # 50px

class Game():
    
    def __init__(self, snake, screen, frames_per_second=4, record_dir=None) -> None:
        self.screen = screen
        self.fps = frames_per_second
        self.clock = pygame.time.Clock()
        self.snake = snake
        if record_dir is None:
            self.record_dir = None
        else:
            self.record_dir = Path(record_dir)
            if not self.record_dir.exists():
                self.record_dir.mkdir(parents=True)
        self.high_score = self.get_current_highscore()
        self.score = 0
        return None

    def run_game(self):
        # initially display the board
        self.is_running = True
        while self.is_running and self.snake.is_alive:
            self.calculate_score()
            self.display_board()
            did_move_happen = False
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if not self.check_for_special_event(event) and event.type == pygame.KEYDOWN:
                    did_move_happen = self.snake.update_from_new_move(event.key)
                    if did_move_happen:
                        # break  # this way only one move happens per click tick
                        pass
            if not did_move_happen:
                # no move was made, so input last event (i.e. keep the snake going in its current direction)
                self.snake.update_from_new_move(self.snake.previous_move)

        # game is over, off with the snake and close the game
        self.save_highscore()
        print(f"Game over!")
        if not self.snake.is_alive:
            self.make_death_animation()
            self.wait_for_user_to_quit()
        else:
            # the snake did not die, but the game was manually exited quit
            self.exit_game()
        return None
    
    def wait_for_user_to_quit(self):
        location = ((self.screen.get_size()[0] // 7), int(self.screen.get_size()[1]/1.25))
        font_size = self.screen.get_size()[0]//20
        self._print_str_to_screen("Press Esc key to quit or Enter to restart", location=location, font_size=font_size, color=(255, 0, 0))
        action = None
        while action is None:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        action = 'quit'
                    elif event.key ==  pygame.K_RETURN:
                        action = 'restart'
                elif event.type == pygame.QUIT:
                    action = 'quit'

                if action == 'quit':
                    print(f'Action happened! {action}')
                    self.exit_game()
                elif action == 'restart':
                    print(f'Action happened! {action}')
                    self.restart_game()

    def check_for_special_event(self, event) -> bool:
        """ checks if the event is a non-key directional command (i.e. quit, pause, speed up/down, etc)
        returns True if special event, else returns False"""
        if event.type == pygame.QUIT:
            self.is_running = False
            return True
        elif event.type == pygame.KEYDOWN:
            # check for pausing:
            if event.key in [pygame.K_p, pygame.K_SLASH, pygame.K_r, pygame.K_SPACE]:
                self.pause_game()
                return True                        
            # check if the a speed up or speed down was requested
            elif event.key in [pygame.K_PERIOD, pygame.K_e]:
                # speed up the game
                self.fps += 1
                return True
            elif event.key in [pygame.K_COMMA, pygame.K_q]:
                # slow down the game
                if self.fps > 1:
                    self.fps -= 1
                return True
        return False

    def display_board(self):
        self.screen.fill((40, 40, 40)) # first reset the screen
        screen_size = list(self.screen.get_size())
        # subtracting the header height from the game screen to get the effective game screen size
        game_screen_size = [screen_size[0], screen_size[1] - HEADER_HEIGHT_OFFSET]  

        # B to screen 
        

        # Render board
        board_to_display = self.snake.prepare_board_for_displaying(game_screen_size)
        pygame_board = pygame.surfarray.make_surface(board_to_display)
        self.screen.blit(pygame_board, (0,HEADER_HEIGHT_OFFSET))

        # Render score
        font = pygame.font.SysFont("Arial", size=int(HEADER_HEIGHT_OFFSET*0.75))
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        score_location = (int(screen_size[0]*0.01), int(HEADER_HEIGHT_OFFSET*0.125))
        self.screen.blit((score_text), score_location)

        # Render high score
        if self.high_score is not None:
            high_score_text = font.render(f"High Score: {self.high_score}", True, (255, 255, 255))
            score_location = (max(score_text.get_width(), screen_size[0]-high_score_text.get_width()),
                              int(HEADER_HEIGHT_OFFSET*0.125))
            self.screen.blit((high_score_text), score_location)

        pygame.display.update()
        return None

    def pause_game(self):

        self._print_str_to_screen("PAUSED", color=(255, 0, 0))
        while True:
            self.clock.tick(1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                    return None
                if event.type == pygame.KEYDOWN:
                    # check if the a speed up or speed down was requested (easy to do while paused)
                    if event.key in [pygame.K_PERIOD, pygame.K_e]:
                            # speed up the game
                            self.fps += 1
                    elif event.key in [pygame.K_COMMA, pygame.K_q]:
                            # slow down the game
                            if self.fps > 1:
                                self.fps -= 1

                    elif event.key in [pygame.K_r, pygame.K_SLASH, pygame.K_SPACE]:  # K_SLASH toggles pause
                        # remove the pause text
                        self.display_board()
                        return None
                    
    def _print_str_to_screen(self, text, location='auto', font_size='auto', color=(255, 255, 255)):
        #TODO: make this work so that "auto" is exactly centered and the text takes up 2/3rds of the screen
        if location == 'auto':
            location = ((self.screen.get_size()[0] // 7), self.screen.get_size()[1]//2)
        if font_size == 'auto':    
            font_size = self.screen.get_size()[0]//8
        font = pygame.font.SysFont("Arial", size=font_size)
        text = font.render(text, True, color)
        self.screen.blit((text), location)
        pygame.display.update()
        return None

    def get_current_highscore(self) -> int:
        if self.record_dir is None:
            return None
        elif not (self.record_dir/'saves.json').exists():
            return None
        else:
            # load saves            
            with open(self.record_dir/'saves.json', 'r') as save_file:
                high_score = json.load(save_file)['high_score']
            return high_score

    def save_highscore(self):
        if self.record_dir is None:
            return False
        else:
            # overwrite save file
            with open(self.record_dir/'saves.json', 'w') as save_file:
                json.dump(dict(high_score=self.high_score), save_file)
            return True

    def calculate_score(self):
        self.score = len(self.snake.body_locations)+1
        # Checking against high score
        if self.high_score is None or self.score > self.high_score:
            print(f'New high score! High score is now: {self.score}')
            self.high_score = self.score
        return None

    def make_death_animation(self):
        self._print_str_to_screen("DEAD!", color=(255, 0, 0))
        return None
        
    def exit_game(self):
        print('DEAD!')
        if self.score is not None:
            print(f'Final score: {self.score}')
        # raise RuntimeError('the snake has stopped running (because it died)')
        pygame.quit()

    def restart_game(self):
        print('Starting new game!')
        start_game()  # then start a new game
        return None

class Snake():
    def __init__(self, board_size=(16, 16), random_seed=42, sprite_location='snake-sprites.png', sprite_size=(16,16)): 
        self.rng = np.random.RandomState(random_seed)
        self.effective_board_size = board_size
        self.sprites = self.get_sprites(sprite_location, sprite_size)
        self.board = np.zeros([3, *board_size], dtype=np.uint8)
        self.previous_head_location = None
        self.previous_move = None
        self.head_location = [board_size[0]//2, board_size[1]//2]
        self.body_locations = []
        self.apple_location = [board_size[0]//2+2, board_size[1]//2+2]
        
        # Sets up the board
        self.initialize_board()
        self.is_alive = True  # ahh, life : )


    def _convert_keypress_to_str(self, keypress_value):
        if keypress_value in [pygame.K_UP, pygame.K_w]:
            return 'up'
            
        elif keypress_value in [pygame.K_DOWN, pygame.K_s]:
            return 'down'
            
        elif keypress_value in [pygame.K_LEFT, pygame.K_a]:
            return 'left'
            
        elif keypress_value in [pygame.K_RIGHT, pygame.K_d]:            
            return 'right'
        else:
            # the move is invalid
            return None
    
    def update_from_new_move(self, new_direction: Union[str, int]):
        """Returns False if move is invalid, otherwise Returns True"""
        self.previous_head_location = self.head_location.copy()
        if isinstance(new_direction, int):
            # convert new_direction to a str \in {"down", "up", "left", "right"} or None if invalid
            new_direction = self._convert_keypress_to_str(new_direction)

        # Recording move
        if new_direction is None:
            return False  # move is invalid
        if new_direction == 'up':
            if self.previous_move == 'down':
                print(f'You cannot go down since you just went up.')
                return False
            self.head_location[1] -= 1
            
        elif new_direction == 'down':
            if self.previous_move == 'up':
                    print(f'You cannot go down since you just went up.')
                    return False
            self.head_location[1] += 1
            
        elif new_direction == 'left':
            if self.previous_move == 'right':
                print(f'You cannot go left since you just went right.')
                return False
            self.head_location[0] -= 1
            
        elif new_direction == 'right':            
            if self.previous_move == 'left':
                print(f'You cannot go right since you just went left.')
                return False
            self.head_location[0] += 1
        
        self.previous_move = new_direction
        
        if self.check_for_death():
            # the snake is dead, long live the apple!
            self.is_alive = False
        else:
            did_eat = self.check_for_growth()
            self.update_body_locations(is_growing=did_eat)
            if did_eat:
                self.make_new_apple()
            self.update_board_arr()

        # TODO: make check for win : )
        return True  # returning True means valid move has been recorded
    
    def update_body_locations(self, is_growing: bool):
        """roll over body locations"""
        if is_growing:
            self.body_locations.append(self.previous_head_location)
            return None
        
        if len(self.body_locations) == 0:
            # the snake has no body :0
            return None

        # if it has a body and is not growing, 
        # remove the oldest body part and add previous head location to the body
        if len(self.body_locations) > 1:
            self.body_locations.pop(0)  # remove the oldest body part
            self.body_locations.append(self.previous_head_location)  # add the previous head to the body
        else:
            self.body_locations = [self.previous_head_location]
        return None
    
    def make_new_apple(self):
        self.apple_location = [self.rng.randint(low=0, high=self.board.shape[-2]),
                               self.rng.randint(low=0, high=self.board.shape[-1])]
        while self.apple_location in self.body_locations + [self.head_location]:
            self.make_new_apple()
        return None
        
    def check_for_death(self):
        """Takes in the current game state, and sees if there are any conflicts (i.e. deaths)"""
        for head_location, board_size in zip(self.head_location, self.board.shape[1:]):
            if head_location < 0 or head_location >= board_size:
                # the snake's head has run into a wall (hopefully it has insurance)
                return True
        if self.head_location in self.body_locations:
            # the snake has run into itself (it's super effective)
            return True
        # if none of the above are True, then the snake has lived to fight another frame
        return False
    
    def check_for_growth(self):
        """Checks to see if the new head location is at the apple"""
        if self.head_location == self.apple_location:
            # print('You grew!')
            return True
        else:
            return False

    ## BOARD FUNCTIONS                
    def initialize_board(self):
        self.board[:, self.head_location[0], self.head_location[1]] = 255
        self.board[0, self.apple_location[0], self.apple_location[1]] = 255
        return None
    
    def update_board_arr(self):
        # TODO: make this more efficient and not re-create the whole board array each time.
        self.board = np.zeros([3, *self.board.shape[1:]], dtype=np.uint8)
        for body_location in self.body_locations:
            self.board[:, body_location[0], body_location[1]] = 255
        self.board[:, self.head_location[0], self.head_location[1]] = 255
        self.board[0, self.apple_location[0], self.apple_location[1]] = 255
        return None

    def prepare_board_for_displaying(self, wanted_size):
        # return resize(np.moveaxis(self.board, 0, -1), output_shape=(wanted_size) + [3, ], 
        #               mode='constant', order=0,
        #               anti_aliasing=False, preserve_range=True).astype(np.uint8)
        display_board  = np.zeros(wanted_size + [3,], dtype=np.uint8)
        # Getting sprites for head
        direction = self._check_body_direction(self.head_location, is_head=True)
        head_type = self._check_body_type(self.head_location, is_head=True)
        head_sprite = self.sprites[f'{head_type}-{direction}']
        # getting apple sprite
        apple_sprite = self.sprites['apple']
        #getting body sprites
        body_sprites = []
        for body_location in self.body_locations:
            direction = self._check_body_direction(body_location)
            body_type = self._check_body_type(body_location)
            body_sprites.append(self.sprites[f'{body_type}-{direction}'])
        all_locations = [self.head_location] + [self.apple_location] + self.body_locations
        all_sprites = [head_sprite] + [apple_sprite] + body_sprites

        # Render the sprites onto the display board
        # TODO: check if this can be made this more efficient?
        for location, sprite in zip(all_locations, all_sprites):
            display_board[location[0]*sprite.shape[0]:(location[0]+1)*sprite.shape[0],
                          location[1]*sprite.shape[1]:(location[1]+1)*sprite.shape[1], ...] = sprite
        
        return display_board

    def _check_body_direction(self, body_location, is_head=False) -> str:
        """Determines the direction a specific body part is going, 
        where `direction` \in {'up', 'right', 'down' left'}"""
        if is_head:
            # the head direction will be whatever direction the snake is moving, unless it is the first move
            # in that case, default to up
            return self.previous_move if self.previous_move is not None else 'up'
        # If not head, a the direction of a body location is determined by the part that is next closest to head
        body_idx = self.body_locations.index(body_location)
        if body_idx == len(self.body_locations)-1:
            # the reference body part (the part that is next closest to the head), is the head
            reference_body_location = self.head_location
        else:
            reference_body_location = self.body_locations[body_idx + 1]
        scaled_location_distance = (
            (np.array(body_location) - np.array(reference_body_location)) * np.array([1, 2]) ).sum()
        if scaled_location_distance > 0:
            if scaled_location_distance == 2:     
                direction = 'left'
            else:  # scaled location distance == 1
                direction = 'down'
        else:
            if scaled_location_distance == -2:
                direction = 'right'
            else:  # scaled location distance == -1
                direction = 'up'
        return direction


    def _check_body_type(self, body_location, is_head=False) -> str:
        """Determines the body type at the current `body_location`. 
        Returns either: `head`, `body`, `tail`, or `unibody`."""
        if is_head:
            # TODO: add a unibody sprite which has a left, right, up, and down
            # # Check if a body does not exist
            # if len(self.body_locations) == 0:
            #     return 'unibody'
            # else:
            #     return 'head'
            return 'head'

        # Check if body part is tail (which is at the beginning of the body array)
        if body_location == self.body_locations[0]:
            return 'tail'
        else:
            return 'body'

    @staticmethod
    def get_sprites(sprite_filepath, sprite_size) -> dict:
        sprite_sheet = plt.imread(sprite_filepath)
        sprites = [[(sprite_sheet[x_idx:x_idx+sprite_size[0], y_idx:y_idx+sprite_size[1], :3] * 255).astype(np.uint8)
                        for y_idx in range(0, sprite_sheet.shape[1], sprite_size[1])]
                            for x_idx in range(0, sprite_sheet.shape[0], sprite_size[0])]
        sprites = sum(sprites, [])  # shape: (n_sprites, width, height)
        sprite_dict = {
            'head-up': sprites[3],
            'head-right': sprites[2],
            'head-down': sprites[1],
            'head-left': sprites[0],
            'body-up': sprites[4],
            'body-down': sprites[4],
            'body-left': sprites[5],
            'body-right': sprites[5],
            'tail-up': sprites[8],
            'tail-right': sprites[7],
            'tail-down': sprites[6],
            'tail-left': sprites[9],
            'apple': sprites[10],
        }
        return sprite_dict

    def update_output_image(self, output_image, output_slice, xy_in_UID):
        # Only update output image if current value is not 0  (i.e. is not empty)
        if xy_in_UID != 0:
            sprite = self.get_sprite_for_unit_id(xy_in_UID)
            output_image[output_slice[0], output_slice[1]] = sprite
        return output_image

    def get_sprite_for_unit_id(self, unit_id):
        if isinstance(unit_id, torch.Tensor):
            unit_id = unit_id.item()
        sprite_idx = UNIT_ID_TO_SPRITE_IDX[unit_id]
        return SPRITES[sprite_idx]

    def expand_and_sprite_image(self, input_image, output_image, w_out, h_out):
        assert input_image.ndim == 2, 'Only 2d (i.e. grayscale) images are supported'
        
        w_in, h_in = input_image.shape[-2:]

        w_scale = int(w_out / w_in)
        h_scale = int(h_out / h_in)
        assert w_scale>1 and h_scale>1, 'Only upscaling is supported.'

        for y_out in range(0, h_out, h_scale):
            for x_out in range(0, w_out, w_scale):
                # Finding the coordinates relative to the input space
                x_in = x_out // w_scale
                y_in = y_out // h_scale

                # finding slice of output pixel space which represents x_in, y_in
                x_in_next = min(x_in+1, w_in)  # making sure we don't go beyond the output image
                y_in_next = min(y_in+1, h_in)  # making sure we don't go beyond the output image
                output_slice = [slice(x_out, (x_in_next*w_scale)),
                                slice(y_out, (y_in_next*h_scale))]

                # get sprite+color which corresponds to value_of_xy_in
                output_image = self.update_output_image(output_image, output_slice)
                
        return output_image

def start_game():
    game_size = (512, 512)
    board_size = (32, 32)
    screen = pygame.display.set_mode((game_size[0], game_size[1]+HEADER_HEIGHT_OFFSET))
    
    snake = Snake(board_size=board_size, sprite_size=(game_size[0]//board_size[0], game_size[1]//board_size[1]),
                  random_seed=None,)
    game = Game(snake, screen, record_dir='./game_saves')
    game.run_game()           



if __name__ == '__main__':      
    pygame.init()
    pygame.display.set_caption('Snake')  
    start_game()
    
