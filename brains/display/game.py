import sys
import time
import pygame
from collections import defaultdict
from collections import namedtuple

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

CellPosition = namedtuple('CellPosition',
                          'layer_id layer_x layer_y left_x right_x top_y bottum_y ')

class Button():
    def __init__(self, x, y, label, function):
        self.x = x
        self.y = y
        self.width = len(label) * 11
        self.height = 20
        self.label = label
        self.function = function

        self.left_x = self.x
        self.right_x = self.x + self.width
        self.top_y = self.y
        self.bottum_y = self.y + self.height

        self._black = (0, 0, 0)
        self._grey = (150, 150, 150)
        self._anti_alias = True
        

    def _in_button(self, x, y):
        in_width = x >= self.left_x and x <= self.right_x
        in_height = y >= self.top_y and y <= self.bottum_y
        return in_width and in_height

    def attempt_press(self, x, y):
        if self._in_button(x, y):
            self.function(self.label)

    def display(self, screen, font):
        surface = pygame.Surface((self.width, self.height,))
        surface.fill(self._grey)
        screen.blit(surface, (self.x, self.y))

        x_text_pos = self.x + 2
        y_text_pos = self.y + 2
        glyfs = font.render(self.label, self._anti_alias,
                            self._black)
        screen.blit(glyfs, (x_text_pos, y_text_pos))
        
    
class GameDisplay():
    def __init__(self, model, environment=None):
        self._model = model
        self._environment = environment
        self._update_ui = True
        self._font_size = 15
        self._sleep_time = 0.01
        self._blue = (0, 0, 255)
        self._black = (0, 0, 0)
        self._yellow = (255, 255, 0)
        self._selected_layer = 'a'
        self._selected_x = 0
        self._selected_y = 0

        pygame.init()
        size = width, height = 1600, 950
        self._screen = pygame.display.set_mode(size)
        self._font = pygame.font.SysFont("monospace", self._font_size)

        #should be enum and set
        self._mode = 0
        self._modes = ["cells", "weights", "none"]
        self._change_mode = False
        self._anti_alias = True
        self._cell_positions = []

        self._buttons = [Button(0, 20, "in_excite", self.update_matrix_to_display),
                         Button(150, 20, "in_inhibit", self.update_matrix_to_display),
                         Button(300, 20, "out_excite", self.update_matrix_to_display),
                         Button(450, 20, "out_inhibit", self.update_matrix_to_display),]
        self._matrix_to_display = "in_excite"

    def update_matrix_to_display(self, name):
        self._matrix_to_display = name

    def _get_mode(self):
        index = self._mode % 3
        return self._modes[index]

    def _in_cell(x, y, cell_position):
        in_width = x >= cell_position.left_x and x <= cell_position.right_x
        in_height = y >= cell_position.top_y and y <= cell_position.bottum_y
        return in_width and in_height

    def _select_cell(self, x, y):
        for cell_position in self._cell_positions:
            if GameDisplay._in_cell(x, y, cell_position):
                self._selected_layer = cell_position.layer_id
                self._selected_x = cell_position.layer_x
                self._selected_y = cell_position.layer_y
                break
        
    # We don't need a display step every model step other options possible
    # 3 types of step pygame, video_output, and model
    def process_step(self, step):
        '''
        Returns if program should exit.
        '''
        mode = self._get_mode()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                self._mode = self._mode + 1
                self._change_mode = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                (x, y, ) = pygame.mouse.get_pos()
                if mode == "cells":
                    self._select_cell(x, y)
                if mode == "weights":
                    for button in self._buttons:
                        button.attempt_press(x, y)
            if event.type == pygame.QUIT:
                return True

        if mode != "none":
            texts = []
            texts.append(f'step: {step}')
            texts.append(f'selected_layer: {self._selected_layer}')
            texts.append(f'selected_x: {self._selected_x}')
            texts.append(f'selected_y: {self._selected_y}')
            drawables, model_texts = self._model.video_output(self._selected_x,
                                                              self._selected_y,
                                                              self._selected_layer)
            texts += model_texts
            if self._environment is not None:
                enivronment_texts = self._environment.video_output(step)
                texts += enivronment_texts
                
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
        return False

    def _update_screen(self, drawables, texts):
        self._screen.fill(self._blue)
        self._display_drawables(drawables)
        x_text_pos = 0
        y_text_pos = 850
        for text in texts:
            label = self._font.render(text, self._anti_alias,
                                      self._black)
            self._screen.blit(label, (x_text_pos, y_text_pos))
            x_text_pos += len(text) * 11
            if x_text_pos > 500:
                x_text_pos = 0
                y_text_pos += 15

    def _display_drawables(self, drawables):
        mode = self._get_mode()
        if mode == "weights":
            for button in self._buttons:
                button.display(self._screen, self._font)
            matrixes_by_label = text_matrixes_from_drawables(drawables)
            x, y = (0, 50,)
            for label, matrix in matrixes_by_label.items():
                if label != self._matrix_to_display:
                    continue
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
            spike_denominator = 3
            spike_height = edge_length // spike_denominator
            voltage_height = edge_length - spike_height
            for drawable in drawables:
                if "strength" in drawable:
                    x_position = drawable["x"] * (edge_length + x_spacing) + border
                    y_position = drawable["y"] * (edge_length + y_spacing) + border
                    cell_position = CellPosition(
                        drawable["layer_id"],
                        drawable["layer_x"],
                        drawable["layer_y"],
                        x_position, x_position + edge_length,
                        y_position, y_position + edge_length)
                    self._cell_positions.append(cell_position)
                    
                    voltage_position = (x_position, y_position + spike_height,)
                    spike_position = (x_position, y_position,)
                    
                    voltage_surface = pygame.Surface((edge_length, voltage_height,))
                    spike_surface = pygame.Surface((edge_length, spike_height,))
                    
                    voltage_color = color_from_strength(drawable["strength"])
                    spike_color = voltage_color
                    if "spike" in drawable and drawable["spike"]:
                        spike_color = self._yellow
                    
                    voltage_surface.fill(voltage_color)
                    spike_surface.fill(spike_color)
                    
                    self._screen.blit(voltage_surface, voltage_position)
                    self._screen.blit(spike_surface, spike_position)

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
