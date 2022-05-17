import sys
import time
import pygame

# should be called potential not strength
def color_from_strength(strength):
    green = 0
    red = 0
    blue = 0
    strength = strength * 255
    if strength > 0:
        red = strength
    if strength > 255:
        red = 255
        blue = 255
    if strength < 0:
        green = -strength
    if strength < -255:
        green = 255
    return red, green, blue

def update_screen(screen, drawables, texts):
    x_spacing = 3
    y_spacing = 3
    border = 3
    edge_length = 10
    blue = (0, 0, 255)
    screen.fill(blue)

    # super inefficient to rebuild the squares but meh
    for drawable in drawables:
        square = pygame.Surface((edge_length, edge_length,))

        x_position = drawable["x"] * (edge_length + x_spacing) + border
        y_position = drawable["y"] * (edge_length + y_spacing) + border
        color = color_from_strength(drawable["strength"])
        try:
            square.fill(color)
        except:
            print(color)
            sys.exit()

        screen.blit(square, (x_position, y_position,))

    screen.blit(square, (x_position, y_position,))
    black = (0, 0, 0)
    x_text_pos = 0
    # waste to load here
    myfont = pygame.font.SysFont("monospace", 20)
    for text in texts:
        label = myfont.render(text, 1, black)
        screen.blit(label, (x_text_pos, 900))
        x_text_pos += 300

class GameDisplay():
    def __init__(self, model, environment=None):
        self._model = model
        self._environment = environment
        pygame.init()
        size = width, height = 1800, 1000
        self._screen = pygame.display.set_mode(size)
        self._update_ui = True

    def process_step(self, step):
        # We don't need a display step every model step other options possible
        # and really we have 3 types of steps
        # one each for pygame, video_output, and model
        # could also record the model then play it?

        turn_off = False
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self._update_ui:
                    self._update_ui = False
                    turn_off = True
                else:
                    self._update_ui = True
            if event.type == pygame.QUIT:
                sys.exit()

        if self._update_ui:
            drawables, texts = self._model.video_output()
            if self._environment is not None:
                enivronment_texts = self._environment.video_output(step)
                texts = texts + enivronment_texts
                
            self._model.video_output()
            texts.append(f'step: {step}')
            update_screen(self._screen, drawables, texts)
            pygame.display.flip()
        
            # really should not need
            time.sleep(0.01)

        if turn_off:
            turn_off = False
            black = (0, 0, 0)
            blue = (0, 0, 255)
            self._screen.fill(black)
            myfont = pygame.font.SysFont("monospace", 20)
            label = myfont.render("display off(runs faster) click anywhere to turn on", 2, blue)
            self._screen.blit(label, (0, 0))
            pygame.display.flip()

            

    def final_output(self):
        pass
