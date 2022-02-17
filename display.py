# should make a model folder and a UI folder
import sys
import time
import pygame
import default_runs

def update_screen(screen, drawables):
    x_spacing = 5
    y_spacing = 5
    border = 5
    height = 20
    width = 20

    # super inefficient to rebuild the squares but meh
    # should also do a spike colour
    for drawable in drawables:
        square = pygame.Surface((20, 20,))
        strength = drawable["strength"] * 255
        green = 0
        red = 0
        blue = 0
        if strength > 0:
            red = strength
        if strength > 255:
            red = 255
            blue = 255
        if strength < 0:
            green = -strength
        if strength < -255:
            green = 255
        color = (red, green, blue)
        try:
            square.fill(color)
        except:
            print(color)
            sys.exit()

        x_position = drawable["x"] * (width + x_spacing) + border
        y_position = drawable["y"] * (height + y_spacing) + border

        screen.blit(square, (x_position, y_position,))
        

def run_model(model, steps, sleep):
    pygame.init()
    size = width, height = 2000, 1000
    # need borders
    screen = pygame.display.set_mode(size)
    red = (255, 0, 0)
    blue = (0, 0, 255)
    screen.fill(blue)

    # do we want max steps if we have an exit?
    for i in range(steps):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # Our i should not be 1 to 1 with pygames i
        # and really we have 3 is pygame, video_output, model step
        # cold also record the model then play it?
        # is that space efficient?
        model.step(i)
        drawables = model.video_output()
        update_screen(screen, drawables)
        pygame.display.flip()
        
        # really should not need
        time.sleep(sleep)
        
def run_example_model():
    model = default_runs.default_example_model()
    run_model(model, 100, 0.1)

def run_simple_model():
    model = default_runs.default_simple_model()
    run_model(model, 1000, 0.01)


def main():
    # run_example_model()
    run_simple_model()

if __name__ == '__main__':
    main()

