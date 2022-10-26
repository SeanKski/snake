from datetime import datetime

import matplotlib.pyplot as plt
import pygame
import numpy as np
from skimage.transform import resize, rescale

#TODO: Add comments, like everywhere :p  (future me will thank current me : )
class Game():
    
    def __init__(self, snake, screen, frames_per_second=3) -> None:
        self.screen = screen
        self.fps = frames_per_second
        self.clock = pygame.time.Clock()
        self.snake = snake
        return None

    def run_game(self):
        # initially display the board
        self.is_running = True
        while self.snake.is_alive and self.is_running:
            self.display_board()
            did_move_happen = False
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if not self.check_for_special_event(event) and event.type == pygame.KEYDOWN:
                    did_move_happen = self.snake.update_from_new_move(event.key)
                    # if did_move_happen:
                        # break  # this way only one move happens per click tick
            if not did_move_happen:
                # no move was made, so input last event (i.e. keep the snake going in its current direction)
                self.snake.update_from_new_move(self.snake.previous_move)

        # game is over, off with the snake and close the game
        self.snake.make_death_animation()
        self.exit_game()
        return None

    def check_for_special_event(self, event) -> bool:
        """ checks if the event is a non-key directional command (i.e. quit, pause, speed up/down, etc)
        returns True if special event, else returns False"""
        if event.type == pygame.QUIT:
            self.is_running = False
            return True
        elif event.type == pygame.KEYDOWN:
            # check for pausing:
            if event.key == pygame.K_p or event.key == pygame.K_SLASH:
                self.pause_game()
                return True                        
            # check if the a speed up or speed down was requested
            elif event.key == pygame.K_PERIOD:
                # speed up the game
                self.fps += 1
                return True
            elif event.key == pygame.K_COMMA:
                # slow down the game
                if self.fps > 1:
                    self.fps -= 1
                return True
        return False

    def display_board(self):
        screen_size = self.screen.get_size()
        board_to_display = self.snake.prepare_board_for_displaying(screen_size)

        self.screen.fill((0, 0, 0)) # first reset the screen
        pygame_board = pygame.surfarray.make_surface(board_to_display)
        self.screen.blit(pygame_board, (0,0))
        pygame.display.update()
        return None

    def pause_game(self):
        font = pygame.font.SysFont("serif", size=self.screen.get_size()[0]//8)
        text_paused = font.render("PAUSED", True, (255, 0, 0))
        pause_location = ((self.screen.get_size()[0] // 7), self.screen.get_size()[1]//2)
        self.screen.blit((text_paused), pause_location)
        pygame.display.update()
        while True:
            self.clock.tick(1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                    return None
                if event.type == pygame.KEYDOWN:
                    # check if the a speed up or speed down was requested (easy to do while paused)
                    if event.key == pygame.K_PERIOD:
                            # speed up the game
                            self.fps += 1
                    elif event.key == pygame.K_COMMA:
                            # slow down the game
                            if self.fps > 1:
                                self.fps -= 1

                    elif event.key == pygame.K_r:
                        # remove the pause text
                        self.display_board()
                        return None
        
    def exit_game(self):
        print('DEAD!')
        # raise RuntimeError('the snake has stopped running (because it died)')
        pygame.QUIT

class Snake():
    def __init__(self, board_size=(16, 16), random_seed=42):        
        self.rng = np.random.RandomState(random_seed)
        self.board = np.zeros([3, *board_size], dtype=np.uint8)
        self.previous_head_location = None
        self.previous_move = None
        self.head_location = [board_size[0]//2, board_size[1]//2]
        self.body_locations = []
        self.apple_location = [board_size[0]//2+2, board_size[1]//2+2]
        
        # Sets up the board
        self.initialize_board()
        self.is_alive = True  # ahh, life : )
    
    def update_from_new_move(self, new_direction: str):
        """Returns False if move is invalid, otherwise Returns True"""
        self.previous_head_location = self.head_location.copy()
        if new_direction == pygame.K_UP:
            if self.previous_move == pygame.K_DOWN:
                print(f'You cannot go down since you just went up.')
                return False
            self.head_location[1] -= 1
            
        elif new_direction == pygame.K_DOWN:
            if self.previous_move == pygame.K_UP:
                    print(f'You cannot go down since you just went up.')
                    return False
            self.head_location[1] += 1
            
        elif new_direction == pygame.K_LEFT:
            if self.previous_move == pygame.K_RIGHT:
                print(f'You cannot go left since you just went right.')
                return False
            self.head_location[0] -= 1
            
        elif new_direction == pygame.K_RIGHT:            
            if self.previous_move == pygame.K_LEFT:
                print(f'You cannot go right since you just went left.')
                return False
            self.head_location[0] += 1
        else:
            # the move is invalid
            return False
        
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

        # TODO: implement a score and update it
        return True
    
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
    
    def initialize_board(self):
        self.board[:, self.head_location[0], self.head_location[1]] = 255
        self.board[0, self.apple_location[0], self.apple_location[1]] = 255
        return None
    
    def update_board_arr(self):
        # TODO: make this more efficient and not re-create the whole image each time.
        self.board = np.zeros([3, *self.board.shape[1:]], dtype=np.uint8)
        for body_location in self.body_locations:
            self.board[:, body_location[0], body_location[1]] = 255
        self.board[:, self.head_location[0], self.head_location[1]] = 255
        self.board[0, self.apple_location[0], self.apple_location[1]] = 255
        return None

    def prepare_board_for_displaying(self, wanted_size):
        return resize(np.moveaxis(self.board, 0, -1), output_shape=(wanted_size) + (3, ), 
                      mode='constant', order=0,
                      anti_aliasing=False, preserve_range=True).astype(np.uint8)
    
    def make_new_apple(self):
        self.apple_location = [self.rng.randint(low=0, high=self.board.shape[0]),
                               self.rng.randint(low=0, high=self.board.shape[1])]
        #TODO: make v this v more efficient############
        for body_location in self.body_locations:
            if self.apple_location == body_location:
                # regenerate the apple so we don't cheat
                self.make_new_apple()
        if self.head_location == self.apple_location:
            self.make_new_apple()
        #TODO: make ^ this ^ more efficient############
        return None
        
    def check_for_death(self):
        """Takes in the current game state, and sees if there are any conflicts (i.e. deaths)"""
        for head_location, board_size in zip(self.head_location, self.board.shape[1:]):
            if head_location < 0 or head_location >= board_size:
                # the snake's head has run into a wall (hopefully it has insurance)
                return True 
        # TODO: make this more efficient
        for body_location in self.body_locations:
            if self.head_location == body_location:
                # the snake has run into itself (it's super effective)
                return True
        # if none of the above are True, then the snake is allowed to live
        return False
    
    def check_for_growth(self):
        """Checks to see if the new head location is at the apple"""
        if self.head_location == self.apple_location:
            # print('You grew!')
            return True
        else:
            return False
    
    def make_death_animation(self):
        # TODO
        return None


if __name__ == '__main__':        
    pygame.init()
    pygame.display.set_caption('Snake')
    screen = pygame.display.set_mode((480,480))
    
    snake = Snake(random_seed=100)
    game = Game(snake, screen)
    game.run_game()
