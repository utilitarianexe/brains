import matplotlib.pyplot as plt
import utils


def decay_pop(steps, epoch_length, decay_rate, start_value, pop_increase):
    x = start_value
    values = []
    for i in range(steps):
        values.append(x)
        x = x * (1 - decay_rate)
        if i % epoch_length == 0:
            x += pop_increase
    return values

values = decay_pop(10000, 300, 0.001, 0, 1)
plt.plot(values)
plt.title(label="hello",
          fontsize=40,
          color="green")
plt.legend()
plt.show()


-(av*al) + (r*al) + av

av  - av*al + (r*al)
