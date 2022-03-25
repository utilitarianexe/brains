import matplotlib.pyplot as plt
import collections

class PlotDisplay():
    def __init__(self, model):
        self._model = model
        self._lines_on_plot_by_label = collections.defaultdict(list)

    def process_step(self):
        model_output = self._model.outputs()
        for label, value in model_output.items():
            self._lines_on_plot_by_label[label].append(value)

    def final_output(self):
        for label, values in self._lines_on_plot_by_label.items():
            plt.plot(values, label=label)
        plt.title(label=self._model.name,
                  fontsize=40,
                  color="green")
        plt.legend()
        plt.show()