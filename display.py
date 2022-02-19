# should make a model folder and a UI folder
import sys
import time
import pygame
import default_runs


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
    x_spacing = 5
    y_spacing = 5
    border = 5
    height = 20
    width = 20
    blue = (0, 0, 255)
    screen.fill(blue)

    # super inefficient to rebuild the squares but meh
    for drawable in drawables:
        square = pygame.Surface((20, 20,))

        x_position = drawable["x"] * (width + x_spacing) + border
        y_position = drawable["y"] * (height + y_spacing) + border
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
    myfont = pygame.font.SysFont("monospace", 15)
    for text in texts:
        label = myfont.render(text, 1, black)
        screen.blit(label, (x_text_pos, 900))
        x_text_pos + 50
        

def run_model(model, steps, sleep):
    pygame.init()
    size = width, height = 1800, 1000
    screen = pygame.display.set_mode(size)

    # do we want max steps if we have an exit?
    for i in range(steps):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # Our i should not be 1 to 1 with pygames i
        # and really we have 3 types of steps
        # one each for pygame, video_output, and model
        # cold also record the model then play it?
        # is that space efficient?
        model.step(i)
        drawables, texts = model.video_output()
        update_screen(screen, drawables, texts)
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

