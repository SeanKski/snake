import re
import matplotlib.pyplot as plt
import pygame
import numpy as np
from skimage.transform import resize, rescale

from datetime import datetime


class SnakeGame():
    def __init__(self, screen, board_size=(16, 16),
                 random_seed=42, frames_per_second=3):
        
        self.screen = screen
        self.fps = frames_per_second
        self.clock = pygame.time.Clock()
        self.rng = np.random.RandomState(random_seed)
        self.board = np.zeros([3, *board_size], dtype=np.uint8)
        self.previous_head_location = None
        self.previous_move = None
        self.head_location = [board_size[0]//2, board_size[1]//2]
        self.body_locations = []
        self.apple_location = [board_size[0]//2+2, board_size[1]//2+2]
        self.running = False
        
    def run_game(self):
        self.initialize_board_image()
        # imshow(self.board)
        # plt.draw()
        # plt.pause(0.0001)
        self.display_board()
        self.running = True
        while self.running:
            did_event_happen = False
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # check for pausing:
                    if event.key == pygame.K_p:
                        self.pause_game()                        
                    # check if the a speed up or speed down was requested
                    if event.key == pygame.K_PERIOD:
                        # speed up the game
                        self.fps += 1
                    elif event.key == pygame.K_COMMA:
                        # slow down the game
                        if self.fps > 1:
                            self.fps -= 1
                    else:
                        did_event_happen = self.update_from_new_move(event.key)
            if not did_event_happen:
                # no move was made, so input last event
                self.update_from_new_move(self.previous_move)
        # game is over, snake is dead!
        self.make_death_animation()
        return None
    
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
            # print(f'{datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]} {new_direction} is an invalid move')
            return False
        
        self.previous_move = new_direction
        
        # checking if the new move is invalid
        is_dead = self.check_for_death()
        if is_dead:
            self.running = False
        else:
            did_eat = self.check_for_growth()
            self.update_body_locations(is_growing=did_eat)
            if did_eat:
                self.make_new_apple()
            self.update_board_arr()
    
        self.display_board()
        return True  # TODO: implement a score and return that?
    
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
    
    def initialize_board_image(self):
        self.board[:, self.head_location[0], self.head_location[1]] = 255
        self.board[0, self.apple_location[0], self.apple_location[1]] = 255
        return None
    
    def update_board_arr(self):
        # TODO: make this more efficient and not re-render the whole image each time.
        self.board = np.zeros([3, *self.board.shape[1:]], dtype=np.uint8)
        for body_location in self.body_locations:
            self.board[:, body_location[0], body_location[1]] = 255
        self.board[:, self.head_location[0], self.head_location[1]] = 255
        self.board[0, self.apple_location[0], self.apple_location[1]] = 255
        return None

    def display_board(self):
        board = np.moveaxis(self.board, 0, -1)
        screen_size = self.screen.get_size()
        resized_board = resize(board, output_shape=(screen_size) + (3, ),
                               mode='constant', order=0,
                               anti_aliasing=False, preserve_range=True).astype(np.uint8)
        self.screen.fill((0, 0, 0)) # first reset the screen
        pygame_board = pygame.surfarray.make_surface(resized_board)
        self.screen.blit(pygame_board, (0,0))
        pygame.display.update()
        return None



    #     self.board[:, self.head_location[0], self.head_location[1]] = 255

    #     if len(self.body_locations) == 0:
    #         self.board[:, self.previous_head_location[0], self.previous_head_location[1]] = 0
    #     elif len(self.body_locations) == 1:
    #         self.board[:, self.body_locations[0][0], self.body_locations[0][1]] = 255


    #     if len(self.body_locations) > 1:
    #         self.board[:, self.body_locations[-1][0], self.body_locations[-1][1]] = 0
    # #         elif len(self.body_locations) == 1:
    # #             pass
    #     else:
    #         self.board[:, self.previous_head_location[0], self.previous_head_location[1]] = 0
    #     self.board[0, self.apple_location[0], self.apple_location[1]] = 255
    #     return None
    
    def make_new_apple(self):
        #TODO: make sure this doesn't get created on a snake body part
        self.apple_location = [self.rng.randint(low=0, high=self.board.shape[0]),
                               self.rng.randint(low=0, high=self.board.shape[1])]
        #TODO: make this more efficient############
        for body_location in self.body_locations:
            if self.apple_location == body_location:
                # regenerate the apple so we don't cheat
                self.make_new_apple()
        if self.head_location == self.apple_location:
            self.make_new_apple()
        #TODO: make this more efficient############
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
                    self.running = False
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
        
    def make_death_animation(self):
        print('DEAD!')
        # raise RuntimeError('the snake has stopped running (because it died)')
        pygame.QUIT


if __name__ == '__main__':        
    pygame.init()
    pygame.display.set_caption('Snake')
    screen = pygame.display.set_mode((480,480))
    
    snake = SnakeGame(screen=screen, random_seed=100)
    snake.run_game()
