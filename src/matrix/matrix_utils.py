
def generate_matrix(ndim):
    # build multi-dim 0-filled array
    if len(ndim) == 1:
        return [0] * ndim[0]
    else:
        result = []
        for i in range(ndim[0]):
            result.append(generate_matrix(ndim[1:]))
        return result


def get_shape(arr):
    # get shape of input multi-dim array
    shape = []
    while type(arr) == list:
        shape.append(len(arr))
        arr = arr[0]
    return shape
