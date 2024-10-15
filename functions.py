def pythagoras(a, b):
    return (a**2 + b**2)**0.5

def round_to_nearest(x, nearest):
    return nearest * round(x/nearest)

def string_to_int_tuple(string):
    string = string.split(",")
    string = [int(item) for item in string]
    return tuple(string)