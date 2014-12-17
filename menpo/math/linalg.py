import numpy as np
from menpo.visualize import print_dynamic, progress_bar_str


def dot_inplace_left(a, b, block_size=1000):
    r"""
    a * b = c where ``a`` will be replaced inplace with ``c``.

    Parameters
    ----------

    a : ndarray, shape (n_big, k)
        First array to dot - assumed to be large. Will be damaged by this
        function call as it is used to store the output inplace.
    b : ndarray, shape (k, n_small), n_small <= k
        The second array to dot - assumed to be small. ``n_small`` must be
        smaller than ``k`` so the result can be stored within the memory space
        of ``a``.
    block_size : int, optional
        The size of the block of ``a`` that will be dotted against ``b`` in
        each iteration. larger block sizes increase the time performance of the
        dot product at the cost of a higher memory overhead for the operation.

    Returns
    -------
    c : ndarray, shape (n_big, n_small)
        The output of the operation. Exactly the same as a memory view onto
        ``a`` (``a[:, :n_small]``) as ``a`` is modified inplace to store the
        result.
    """
    (n_big, k_a), (k_b, n_small) = a.shape, b.shape
    if k_a != k_b:
        raise ValueError('Cannot dot {} * {}'.format(a.shape, b.shape))
    if n_small > k_a:
        raise ValueError('Cannot dot inplace left - '
                         'b.shape[1] ({}) > a.shape[1] '
                         '({})'.format(n_small, k_a))
    for i in range(0, n_big, block_size):
        j = i + block_size
        a[i:j, :n_small] = a[i:j].dot(b)
    return a[:, :n_small]


def dot_inplace_right(a, b, block_size=1000):
    r"""
    a * b = c where ``b`` will be replaced inplace with ``c``.

    Parameters
    ----------

    a : ndarray, shape (n_small, k), n_small <= k
        The first array to dot - assumed to be small. ``n_small`` must be
        smaller than ``k`` so the result can be stored within the memory space
        of ``b``.
    b : ndarray, shape (k, n_big)
        Second array to dot - assumed to be large. Will be damaged by this
        function call as it is used to store the output inplace.
    block_size : int, optional
        The size of the block of ``b`` that ``a`` will be dotted against
        in each iteration. larger block sizes increase the time performance of
        the dot product at the cost of a higher memory overhead for the
        operation.

    Returns
    -------
    c : ndarray, shape (n_small, n_big)
        The output of the operation. Exactly the same as a memory view onto
        ``b`` (``b[:n_small]``) as ``b`` is modified inplace to store the
        result.
    """
    (n_small, k_a), (k_b, n_big) = a.shape, b.shape
    if k_a != k_b:
        raise ValueError('Cannot dot {} * {}'.format(a.shape, b.shape))
    if n_small > k_b:
        raise ValueError('Cannot dot inplace right - '
                         'a.shape[1] ({}) > b.shape[0] '
                         '({})'.format(n_small, k_b))
    for i in range(0, n_big, block_size):
        j = i + block_size
        b[:n_small, i:j] = a.dot(b[:, i:j])
    return b[:n_small]


def as_matrix(vectorizables, length=None, return_template=False, verbose=False):
    r"""
    Create a matrix from a list/generator of :map:`Vectorizable` objects.
    All the objects in the list **must** be the same size when vectorized.

    Consider using a generator if the matrix you are creating is large and
    passing the length of the generator explicitly.

    Parameters
    ----------
    vectorizables : `list` or generator if :map:`Vectorizable` objects
        A list or generator of objects that supports the vectorizable interface
    length : `int`, optional
        Length of the vectorizable list. Useful if you are passing a generator
        with a known length.
    verbose : `bool`, optional
        If ``True``, will print the progress of building the matrix.
    return_template : `bool`, optional
        If ``True``, will return the first element of the list/generator, which
        was used as the template. Useful if you need to map back from the
        matrix to a list of vectorizable objects.

    Returns
    -------
    M : (length, n_features) `ndarray`
        Every row is an element of the list.
    template : :map:`Vectorizable`, optional
        If ``return_template == True``, will return the template used to
        build the matrix `M`.
    """
    # get the first element as the template and use it to configure the
    # data matrix
    if length is None:
        # samples is a list
        length = len(vectorizables)
        template = vectorizables[0]
        vectorizables = vectorizables[1:]
    else:
        # samples is an iterator
        template = next(vectorizables)
    n_features = template.n_parameters
    template_vector = template.as_vector()

    data = np.zeros((length, n_features), dtype=template_vector.dtype)
    if verbose:
        print('Allocated data matrix {:.2f}'
              'GB'.format(data.nbytes / 2 ** 30))

    # now we can fill in the first element from the template
    data[0] = template_vector
    del template_vector

    # 1-based as we have the template vector set already
    for i, sample in enumerate(vectorizables, 1):
        if i >= length:
            break
        if verbose:
            print_dynamic(
                'Building data matrix from {} samples - {}'.format(
                    length,
                    progress_bar_str(float(i + 1) / length, show_bar=True)))
        data[i] = sample.as_vector()

    if return_template:
        return data, template
    else:
        return data


def from_matrix(matrix, template, as_generator=False):
    r"""
    Create a list/generator from a matrix given a template :map:`Vectorizable`
    objects as a template. The ``from_vector`` method will be used to
    reconstruct each object.

    If you are short on memory, consider using the ``as_generator`` argument.

    Parameters
    ----------
    matrix : (n_items, n_features) `ndarray`
        A matrix whereby every *row* represents the data of a vectorizable
        object.
    template : :map:`Vectorizable`
        The template object to use to reconstruct each row of the matrix with.
    as_generator : `bool`, optional
        If ``True``, will return a generator as opposed to a list (for memory
        efficiency).

    Returns
    -------
    M : (length, n_features) `ndarray`
        Every row is an element of the list.
    template : :map:`Vectorizable`, optional
        If ``return_template == True``, will return the template used to
        build the matrix `M`.
    """
    vectorizables = (template.from_vector(row) for row in matrix)
    if as_generator:
        return vectorizables
    else:
        return list(vectorizables)
