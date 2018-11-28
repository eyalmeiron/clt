class Colors(object):

    _color_index = 0
    _colors = [
        'yellow',
        'black',
        'cyan',
        'magenta',
        'white',
        'reset',
        'blue',
        'red',
        'green',
    ]

    # get the next color by round robin
    @staticmethod
    def get_color():
        color = Colors._colors[Colors._color_index]
        Colors._color_index = (Colors._color_index + 1) % len(Colors._colors)
        return color

    @staticmethod
    def get_colors(holders):
        holders_colors = {}
        prev_color_index = Colors._color_index
        Colors._color_index = 0
        for holder in holders:
            holders_colors[holder] = Colors.get_color()
        Colors._color_index = prev_color_index
        return holders_colors

    @staticmethod
    def reset_color_index():
        Colors._color_index = 0
