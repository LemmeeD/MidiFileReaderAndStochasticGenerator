import numpy as np


def get_jump_chain(Q):
    jump_chain = np.zeros(Q.shape)
    for i in range(Q.shape[0]):
        if not np.sum(Q[i, :]) < 0.000001:
            raise Exception
    for i in range(Q.shape[0]):
        for j in range(Q.shape[1]):
            if i != j:
                jump_chain[i, j] = -Q[i, j] / Q[i, i]
            else:
                jump_chain[i, j] = 0
    return jump_chain


def get_uniformized_transition_matrix(Q):
    uniformized_transition_matrix = np.zeros(Q.shape)
    sup = -1
    for i in range(Q.shape[0]):
        for j in range(Q.shape[1]):
            if Q[i, j] > 0:
                if Q[i, j] >= sup:
                    sup = Q[i, j]
    if sup <= 0:
        raise Exception

    for i in range(Q.shape[0]):
        Q[i, i] = -Q[i, i]
    sup = np.amax(Q)
    for i in range(Q.shape[0]):
        Q[i, i] = -Q[i, i]

    for i in range(Q.shape[0]):
        for j in range(Q.shape[1]):
            uniformized_transition_matrix[i, j] = Q[i, j] / sup
    uniformized_transition_matrix = uniformized_transition_matrix + np.identity(Q.shape[0])
    return uniformized_transition_matrix


def sample_from_uniformized_transition_matrix(row, row_probs):
    x = np.random.choice(a=row, p=row_probs)
    i = row.index(x)
    return x, i