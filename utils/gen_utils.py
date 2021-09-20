from fractions import Fraction
import numpy as np


def remove_duplicates_from_list(l):
    return list(dict.fromkeys(l))


def remove_None_elements_from_list(a):
    return list(filter(lambda e: e is not None, a))


def get_note_duration_as_number(fraction_string):
    try:
        result = float(fraction_string)
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


def find_first_uninitialized_element_index(ndarray):
    for i, elem in enumerate(ndarray):
        if elem is None or elem == 0:
            return i
    return None


def element_most_occurrences(list):
    dataset = remove_duplicates_from_list(list)
    occur = []
    for i in range(len(dataset)):
        occur.append(0)
    for i in range(len(list)):
        for j in range(len(dataset)):
            if list[i] == dataset[j]:
                occur[j] += 1
                break
    n = np.amax(occur)
    return get_note_duration_as_number(dataset[occur.index(n)])