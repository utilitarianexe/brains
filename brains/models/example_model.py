class ExampleModel:
    def __init__(self):
        self.name = "Example Model"
        self._x = 0

    def step(self, step, environment):
        self._x += 0.1
        if self._x > 1:
            self._x = -1

    def video_output(self):
        # maybe make a class
        return ([{"name":"example name", "x": 10, "y":10, "strength": self._x}],
                ["example text"],)

    def outputs(self):
        #spelling?
        return {"increment": self._x, "constant": 0}
