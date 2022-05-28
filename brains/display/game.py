import sys
import time
import pygame
from collections import defaultdict

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


def text_matrixes_from_drawables(drawables):
    matrix_drawables_by_label = defaultdict(list)
    for drawable in drawables:
        if "text" not in drawable:
            continue
        matrix_drawables_by_label[drawable["matrix_label"]].append(drawable)
            
    matrixes_by_label = {}
    for label, drawables in matrix_drawables_by_label.items():
        matrixes_by_label[label] = text_matrix_from_drawables(drawables)
    return matrixes_by_label

# not using self
def text_matrix_from_drawables(drawables):
    max_x = 1
    max_y = 1
    text_by_x_by_y = defaultdict(lambda: defaultdict(str))
    for drawable in drawables:
        if drawable["x"] > max_x:
            max_x = drawable["x"]
        if drawable["y"] > max_y:
            max_y = drawable["y"]
        text_by_x_by_y[drawable["x"]][drawable["y"]] = drawable["text"]

    cells = []
    for i in range(max_y + 1):
        row = []
        for j in range(max_x + 1):
            row.append(text_by_x_by_y[j][i])
        cells.append(row)
    return cells

class GameDisplay():
    def __init__(self, model, environment=None):
        self._model = model
        self._environment = environment
        self._update_ui = True
        self._font_size = 15
        self._sleep_time = 0.01
        self._blue = (0, 0, 255)
        self._black = (0, 0, 0)


        pygame.init()
        size = width, height = 1600, 950
        self._screen = pygame.display.set_mode(size)
        self._font = pygame.font.SysFont("monospace", self._font_size)

        #should be enum and set
        self._mode = 0
        self._modes = ["cells", "weights", "none"]
        self._change_mode = False
        self._anti_alias = True

    def _get_mode(self):
        index = self._mode % 3
        return self._modes[index]

    # We don't need a display step every model step other options possible
    # 3 types of step pygame, video_output, and model
    def process_step(self, step):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._mode = self._mode + 1
                self._change_mode = True
            if event.type == pygame.QUIT:
                sys.exit()

        mode = self._get_mode()
        if mode != "none":
            drawables, texts = self._model.video_output()
            if self._environment is not None:
                enivronment_texts = self._environment.video_output(step)
                texts = texts + enivronment_texts
                
            texts.append(f'step: {step}')
            self._update_screen(drawables, texts)
            pygame.display.flip()
        
            # really should not need
            time.sleep(self._sleep_time)

        if mode == "none":
            if self._change_mode:
                self._screen.fill(self._black)
                text = "display off(runs faster) click anywhere to turn on"
                label = self._font.render(text,
                                          self._anti_alias,
                                          self._blue)
                self._screen.blit(label, (0, 0))
                pygame.display.flip()

        self._change_mode = False

    def _update_screen(self, drawables, texts):
        self._screen.fill(self._blue)
        self._display_drawables(drawables)
        x_text_pos = 0
        for text in texts:
            label = self._font.render(text, self._anti_alias,
                                      self._black)
            self._screen.blit(label, (x_text_pos, 900))
            x_text_pos += 300

    def _display_drawables(self, drawables):
        mode = self._get_mode()
        if mode == "weights":
            matrixes_by_label = text_matrixes_from_drawables(drawables)
            x, y = (0, 0,)
            for label, matrix in matrixes_by_label.items():
                text = self._font.render(label, self._anti_alias, self._black)
                self._screen.blit(text, (x, y))
                y += 20
                _, y = self._display_text_matrix(matrix, x, y)
                y += 20

        if mode == "cells":
            x_spacing = 3
            y_spacing = 3
            border = 10
            edge_length = 10
            for drawable in drawables:
                if "strength" in drawable:
                    x_position = drawable["x"] * (edge_length + x_spacing) + border
                    y_position = drawable["y"] * (edge_length + y_spacing) + border
                    position = (x_position, y_position,)
                    square = pygame.Surface((edge_length, edge_length,))
                    color = color_from_strength(drawable["strength"])
                    square.fill(color)
                    self._screen.blit(square, position)

    def _display_text_matrix(self,
                             text_matrix, matrix_x_position , matrix_y_position,
                             x_padding = 2, y_padding = 2,
                             color=(0, 0, 0)):
        max_cell_length = 1
        for row in text_matrix:
            for cell in row:
                if len(cell) > max_cell_length:
                    max_cell_length = len(cell)
    
        cell_y_position = matrix_y_position
        for row in text_matrix:
            cell_x_position = matrix_x_position
            for cell in row:
                label = self._font.render(cell, self._anti_alias, color)
                self._screen.blit(label, (cell_x_position, cell_y_position))
                cell_x_position += max_cell_length * self._font_size / 1.5 + x_padding
            cell_y_position += y_padding + self._font_size

        return cell_x_position, cell_y_position


    def final_output(self):
        pass
