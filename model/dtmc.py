import numpy as np
import utils


def create_transition_matrix_from_sequence(sequence):
    pool = utils.remove_duplicates_from_list(sequence)  # maintains the order of appearing elements
    # if last element has no transition and is the only one appearing in the entire sequence
    last_element = sequence[-1]
    if sequence.count(last_element) == 1:
        pool.remove(last_element)
        l = 2
    else:
        l = 1
    # actual transition matrix creation
    transition_matrix = np.zeros((len(pool), len(pool)))
    for i in range(len(sequence)-l):
        transition_matrix[pool.index(sequence[i]), pool.index(sequence[i+1])] += 1
    for i in range(len(pool)):
        row_tot = 0
        for j in range(len(pool)):
            row_tot = row_tot + transition_matrix[i, j]
        for j in range(len(pool)):
            transition_matrix[i, j] = transition_matrix[i, j] / row_tot
    if is_well_formatted(transition_matrix):
        return transition_matrix, pool
    else:
        print("DEBUG: transition_matrix is not well defined")
        raise Exception


def sample_pitch_duration_attack(pitches, p_pitches, durations, p_durations, attacks, p_attacks):
    p = np.random.choice(a=pitches, p=p_pitches)
    d = utils.get_note_duration_as_number(np.random.choice(a=durations, p=p_durations))
    a = utils.get_note_duration_as_number(np.random.choice(a=attacks, p=p_attacks))
    return p, d, a      # numbers


def generate_equiprobable_initial_probability_vector(dataset_pool):
    result = []
    for i in range(len(dataset_pool)):
        result.append(1 / len(dataset_pool))


def is_well_formatted(matrix):
    if type(matrix) is list:
        quad = (len(matrix[0][:]) == len(matrix[:][0]))
        for i in range(len(matrix[0][:])):
            row_tot = 0
            for j in range(len(matrix[:][0])):
                row_tot = row_tot + matrix[i][j]
            if row_tot != 1:
                return False
    else:
        quad = (matrix.shape[0] == matrix.shape[1])
        for i in range(matrix.shape[0]):
            row_tot = 0
            for j in range(matrix.shape[1]):
                row_tot = row_tot + matrix[i, j]
            if row_tot - 1 > 0.0001:
                return False
    # return (not np.any(np.sum(matrix, axis=1) != 1)) and (quad)
    return quad
