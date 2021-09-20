import numpy as np
from utils import gen_utils


def control_last_element_transition(sequence, pool):
    # if last element has no transition and is the only one appearing in the entire sequence
    last_element = sequence[-1]
    num_indexes_to_eliminate = 0
    if sequence.count(last_element) == 1:
        pool.remove(last_element)
        sequence.pop(-1)
        num_indexes_to_eliminate = 2
    else:
        num_indexes_to_eliminate = 1
    return num_indexes_to_eliminate, pool

def create_transition_matrix_from_sequence(sequence):
    pool = gen_utils.remove_duplicates_from_list(sequence)  # maintains the order of appearing elements
    num_indexes_to_eliminate = 0
    temp = 0
    while temp != 1:
        temp, pool = control_last_element_transition(sequence, pool)
        num_indexes_to_eliminate = num_indexes_to_eliminate + temp
    # actual transition matrix creation
    transition_matrix = np.zeros((len(pool), len(pool)))
    for i in range(len(sequence)-num_indexes_to_eliminate):
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


def sample(dataset, probs):
    result = np.random.choice(a=dataset, p=probs)
    return result, dataset.index(result)


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


def compute_heuristic_coeff(sequence):
    deltas = []
    for i in range(len(sequence)-1):
        deltas.append(np.abs(sequence[i+1]-sequence[i]))
    max = np.amax(sequence)
    min = np.amin(sequence)
    return (np.mean(deltas) + np.abs(max-min)) / 2


def is_lead_melody(coeff_heuristic):
    return coeff_heuristic < 12.3


# to be deleted?
def compute_heuristic_coeff2(duration_sequence, bpm):
    threshold = 110 / (1/2)
    d = gen_utils.element_most_occurrences(duration_sequence)
    if bpm/d >= threshold:
        return threshold
    else:
        return bpm/d