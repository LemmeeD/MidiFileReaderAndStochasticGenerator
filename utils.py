from fractions import Fraction


def remove_duplicates_from_list(l):
    return list(dict.fromkeys(l))


def remove_None_elements_from_list(a):
    return list(filter(lambda e: e is not None, a))


def get_note_duration_as_number(fraction_string):
    try:
        result = int(fraction_string)
        return result
    except ValueError:
        index = fraction_string.find("/")
        numerator = int(fraction_string[0:index])
        denominator = int(fraction_string[index+1:])
        return (numerator / denominator)


def get_note_duration_as_string_fraction(float_number):
    # f = float_number.as_integer_ratio()
    return str(Fraction(float_number).limit_denominator(32))


def convert_ticks_to_fraction_string(tot_ticks, ticks_per_beat):
    return str(Fraction(tot_ticks / ticks_per_beat).limit_denominator(32))