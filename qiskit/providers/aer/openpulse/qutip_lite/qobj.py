# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# This file is part of QuTiP: Quantum Toolbox in Python.
#
#    Copyright (c) 2011 and later, Paul D. Nation and Robert J. Johansson.
#    All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are
#    met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of the QuTiP: Quantum Toolbox in Python nor the names
#       of its contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
#    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#    PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###############################################################################
# pylint: disable=invalid-name, redefined-outer-name, no-name-in-module
# pylint: disable=import-error, unused-import

"""The Quantum Object (Qobj) class, for representing quantum states and
operators, and related functions.
"""

__all__ = ['Qobj']

import warnings
import types
import builtins

from itertools import zip_longest
# import math functions from numpy.math: required for td string evaluation
import numpy as np
from numpy import (arccos, arccosh, arcsin, arcsinh, arctan, arctan2, arctanh,
                   ceil, copysign, cos, cosh, degrees, e, exp, expm1, fabs,
                   floor, fmod, frexp, hypot, isinf, isnan, ldexp, log, log10,
                   log1p, modf, pi, radians, sin, sinh, sqrt, tan, tanh, trunc)
import scipy.sparse as sp
import scipy.linalg as la
from qiskit.providers.aer.version import __version__
from .settings import (auto_tidyup, auto_tidyup_dims, atol, auto_tidyup_atol)
from .fastsparse import fast_csr_matrix, fast_identity
from .sparse import (sp_eigs, sp_expm, sp_fro_norm, sp_max_norm,
                     sp_one_norm, sp_L2_norm)
from .dimensions import type_from_dims, enumerate_flat, collapse_dims_super
from .cy.spmath import (zcsr_transpose, zcsr_adjoint, zcsr_isherm,
                        zcsr_trace, zcsr_proj, zcsr_inner)
from .cy.spmatfuncs import zcsr_mat_elem
from .cy.sparse_utils import cy_tidyup


class Qobj():
    """A class for representing quantum objects, such as quantum operators
    and states.

    The Qobj class is the QuTiP representation of quantum operators and state
    vectors. This class also implements math operations +,-,* between Qobj
    instances (and / by a C-number), as well as a collection of common
    operator/state operations.  The Qobj constructor optionally takes a
    dimension ``list`` and/or shape ``list`` as arguments.

    Attributes
    ----------
    data : array_like
        Sparse matrix characterizing the quantum object.
    dims : list
        List of dimensions keeping track of the tensor structure.
    shape : list
        Shape of the underlying `data` array.
    type : str
        Type of quantum object: 'bra', 'ket', 'oper', 'operator-ket',
        'operator-bra', or 'super'.
    superrep : str
        Representation used if `type` is 'super'. One of 'super'
        (Liouville form) or 'choi' (Choi matrix with tr = dimension).
    isherm : bool
        Indicates if quantum object represents Hermitian operator.
    isunitary : bool
        Indictaes if quantum object represents unitary operator.
    iscp : bool
        Indicates if the quantum object represents a map, and if that map is
        completely positive (CP).
    ishp : bool
        Indicates if the quantum object represents a map, and if that map is
        hermicity preserving (HP).
    istp : bool
        Indicates if the quantum object represents a map, and if that map is
        trace preserving (TP).
    iscptp : bool
        Indicates if the quantum object represents a map that is completely
        positive and trace preserving (CPTP).
    isket : bool
        Indicates if the quantum object represents a ket.
    isbra : bool
        Indicates if the quantum object represents a bra.
    isoper : bool
        Indicates if the quantum object represents an operator.
    issuper : bool
        Indicates if the quantum object represents a superoperator.
    isoperket : bool
        Indicates if the quantum object represents an operator in column vector
        form.
    isoperbra : bool
        Indicates if the quantum object represents an operator in row vector
        form.

    Methods
    -------
    copy()
        Create copy of Qobj
    conj()
        Conjugate of quantum object.
    cosm()
        Cosine of quantum object.
    dag()
        Adjoint (dagger) of quantum object.
    dnorm()
        Diamond norm of quantum operator.
    dual_chan()
        Dual channel of quantum object representing a CP map.
    eigenenergies(sparse=False, sort='low', eigvals=0, tol=0, maxiter=100000)
        Returns eigenenergies (eigenvalues) of a quantum object.
    eigenstates(sparse=False, sort='low', eigvals=0, tol=0, maxiter=100000)
        Returns eigenenergies and eigenstates of quantum object.
    expm()
        Matrix exponential of quantum object.
    full(order='C')
        Returns dense array of quantum object `data` attribute.
    groundstate(sparse=False, tol=0, maxiter=100000)
        Returns eigenvalue and eigenket for the groundstate of a quantum
        object.
    matrix_element(bra, ket)
        Returns the matrix element of operator between `bra` and `ket` vectors.
    norm(norm='tr', sparse=False, tol=0, maxiter=100000)
        Returns norm of a ket or an operator.
    proj()
        Computes the projector for a ket or bra vector.
    sinm()
        Sine of quantum object.
    sqrtm()
        Matrix square root of quantum object.
    tidyup(atol=1e-12)
        Removes small elements from quantum object.
    tr()
        Trace of quantum object.
    trans()
        Transpose of quantum object.
    transform(inpt, inverse=False)
        Performs a basis transformation defined by `inpt` matrix.
    trunc_neg(method='clip')
        Removes negative eigenvalues and returns a new Qobj that is
        a valid density operator.
    unit(norm='tr', sparse=False, tol=0, maxiter=100000)
        Returns normalized quantum object.

    """
    __array_priority__ = 100  # sets Qobj priority above numpy arrays

    # pylint: disable=dangerous-default-value, redefined-builtin
    def __init__(self, inpt=None, dims=[[], []], shape=[],
                 type=None, isherm=None, copy=True,
                 fast=False, superrep=None, isunitary=None):
        """
        Qobj constructor.

        Args:
            inpt (ndarray): Input array or matrix data.
            dims (list): List of Qobj dims.
            shape (list):  shape of underlying data.
            type (str): Is object a ket, bra, oper, super.
            isherm (bool): Is object Hermitian.
            copy (bool): Copy input data.
            fast (str or bool): Fast object instantiation.
            superrep (str): Type of super representaiton.
            isunitary (bool): Is object unitary.

        Raises:
            Exception: Something bad happened.
        """

        self._isherm = isherm
        self._type = type
        self.superrep = superrep
        self._isunitary = isunitary

        if fast == 'mc':
            # fast Qobj construction for use in mcsolve with ket output
            self._data = inpt
            self.dims = dims
            self._isherm = False
            return

        if fast == 'mc-dm':
            # fast Qobj construction for use in mcsolve with dm output
            self._data = inpt
            self.dims = dims
            self._isherm = True
            return

        if isinstance(inpt, Qobj):
            # if input is already Qobj then return identical copy

            self._data = fast_csr_matrix((inpt.data.data, inpt.data.indices,
                                          inpt.data.indptr),
                                         shape=inpt.shape, copy=copy)

            if not np.any(dims):
                # Dimensions of quantum object used for keeping track of tensor
                # components
                self.dims = inpt.dims
            else:
                self.dims = dims

            self.superrep = inpt.superrep
            self._isunitary = inpt._isunitary

        elif inpt is None:
            # initialize an empty Qobj with correct dimensions and shape

            if any(dims):
                N, M = np.prod(dims[0]), np.prod(dims[1])
                self.dims = dims

            elif shape:
                N, M = shape
                self.dims = [[N], [M]]

            else:
                N, M = 1, 1
                self.dims = [[N], [M]]

            self._data = fast_csr_matrix(shape=(N, M))

        elif isinstance(inpt, (list, tuple)):
            # case where input is a list
            data = np.array(inpt)
            if len(data.shape) == 1:
                # if list has only one dimension (i.e [5,4])
                data = data.transpose()

            _tmp = sp.csr_matrix(data, dtype=complex)
            self._data = fast_csr_matrix((_tmp.data, _tmp.indices, _tmp.indptr),
                                         shape=_tmp.shape)
            if not np.any(dims):
                self.dims = [[int(data.shape[0])], [int(data.shape[1])]]
            else:
                self.dims = dims

        elif isinstance(inpt, np.ndarray) or sp.issparse(inpt):
            # case where input is array or sparse
            if inpt.ndim == 1:
                inpt = inpt[:, np.newaxis]

            do_copy = copy
            if not isinstance(inpt, fast_csr_matrix):
                _tmp = sp.csr_matrix(inpt, dtype=complex, copy=do_copy)
                _tmp.sort_indices()  # Make sure indices are sorted.
                do_copy = 0
            else:
                _tmp = inpt
            self._data = fast_csr_matrix((_tmp.data, _tmp.indices, _tmp.indptr),
                                         shape=_tmp.shape, copy=do_copy)

            if not np.any(dims):
                self.dims = [[int(inpt.shape[0])], [int(inpt.shape[1])]]
            else:
                self.dims = dims

        elif isinstance(inpt, (int, float, complex,
                               np.integer, np.floating, np.complexfloating)):
            # if input is int, float, or complex then convert to array
            _tmp = sp.csr_matrix([[inpt]], dtype=complex)
            self._data = fast_csr_matrix((_tmp.data, _tmp.indices, _tmp.indptr),
                                         shape=_tmp.shape)
            if not np.any(dims):
                self.dims = [[1], [1]]
            else:
                self.dims = dims

        else:
            warnings.warn("Initializing Qobj from unsupported type: %s" %
                          builtins.type(inpt))
            inpt = np.array([[0]])
            _tmp = sp.csr_matrix(inpt, dtype=complex, copy=copy)
            self._data = fast_csr_matrix((_tmp.data, _tmp.indices, _tmp.indptr),
                                         shape=_tmp.shape)
            self.dims = [[int(inpt.shape[0])], [int(inpt.shape[1])]]

        if type == 'super':
            # Type is not super, i.e. dims not explicitly passed, but oper shape
            if dims == [[], []] and self.shape[0] == self.shape[1]:
                sub_shape = np.sqrt(self.shape[0])
                # check if root of shape is int
                if (sub_shape % 1) != 0:
                    raise Exception('Invalid shape for a super operator.')

                sub_shape = int(sub_shape)
                self.dims = [[[sub_shape], [sub_shape]]] * 2

        if superrep:
            self.superrep = superrep
        else:
            if self.type == 'super' and self.superrep is None:
                self.superrep = 'super'

        # clear type cache
        self._type = None

    def copy(self):
        """Create identical copy"""
        return Qobj(inpt=self)

    def get_data(self):
        """Gets underlying data."""
        return self._data

    # Here we perfrom a check of the csr matrix type during setting of Q.data
    def set_data(self, data):
        """Data setter
        """
        if not isinstance(data, fast_csr_matrix):
            raise TypeError('Qobj data must be in fast_csr format.')

        self._data = data
    data = property(get_data, set_data)

    def __add__(self, other):
        """
        ADDITION with Qobj on LEFT [ ex. Qobj+4 ]
        """
        self._isunitary = None

        if not isinstance(other, Qobj):
            if isinstance(other, (int, float, complex, np.integer,
                                  np.floating, np.complexfloating, np.ndarray,
                                  list, tuple)) or sp.issparse(other):
                other = Qobj(other)
            else:
                return NotImplemented

        if np.prod(other.shape) == 1 and np.prod(self.shape) != 1:
            # case for scalar quantum object
            dat = other.data[0, 0]
            if dat == 0:
                return self

            out = Qobj()

            if self.type in ['oper', 'super']:
                out.data = self.data + dat * fast_identity(
                    self.shape[0])
            else:
                out.data = self.data
                out.data.data = out.data.data + dat

            out.dims = self.dims

            if auto_tidyup:
                out.tidyup()

            if isinstance(dat, (int, float)):
                out._isherm = self._isherm
            else:
                # We use _isherm here to prevent recalculating on self and
                # other, relying on that bool(None) == False.
                out._isherm = (True if self._isherm and other._isherm
                               else out.isherm)

            out.superrep = self.superrep

            return out

        elif np.prod(self.shape) == 1 and np.prod(other.shape) != 1:
            # case for scalar quantum object
            dat = self.data[0, 0]
            if dat == 0:
                return other

            out = Qobj()
            if other.type in ['oper', 'super']:
                out.data = dat * fast_identity(other.shape[0]) + other.data
            else:
                out.data = other.data
                out.data.data = out.data.data + dat
            out.dims = other.dims

            if auto_tidyup:
                out.tidyup()

            if isinstance(dat, complex):
                out._isherm = out.isherm
            else:
                out._isherm = self._isherm

            out.superrep = self.superrep

            return out

        elif self.dims != other.dims:
            raise TypeError('Incompatible quantum object dimensions')

        elif self.shape != other.shape:
            raise TypeError('Matrix shapes do not match')

        else:  # case for matching quantum objects
            out = Qobj()
            out.data = self.data + other.data
            out.dims = self.dims
            if auto_tidyup:
                out.tidyup()

            if self.type in ['ket', 'bra', 'operator-ket', 'operator-bra']:
                out._isherm = False
            elif self._isherm is None or other._isherm is None:
                out._isherm = out.isherm
            elif not self._isherm and not other._isherm:
                out._isherm = out.isherm
            else:
                out._isherm = self._isherm and other._isherm

            if self.superrep and other.superrep:
                if self.superrep != other.superrep:
                    msg = ("Adding superoperators with different " +
                           "representations")
                    warnings.warn(msg)

                out.superrep = self.superrep

            return out

    def __radd__(self, other):
        """
        ADDITION with Qobj on RIGHT [ ex. 4+Qobj ]
        """
        return self + other

    def __sub__(self, other):
        """
        SUBTRACTION with Qobj on LEFT [ ex. Qobj-4 ]
        """
        return self + (-other)

    def __rsub__(self, other):
        """
        SUBTRACTION with Qobj on RIGHT [ ex. 4-Qobj ]
        """
        return (-self) + other

    # pylint: disable=too-many-return-statements
    def __mul__(self, other):
        """
        MULTIPLICATION with Qobj on LEFT [ ex. Qobj*4 ]
        """
        self._isunitary = None

        if isinstance(other, Qobj):
            if self.dims[1] == other.dims[0]:
                out = Qobj()
                out.data = self.data * other.data
                dims = [self.dims[0], other.dims[1]]
                out.dims = dims
                if auto_tidyup:
                    out.tidyup()
                if (auto_tidyup_dims and not
                        isinstance(dims[0][0], list) and not
                        isinstance(dims[1][0], list)):
                    # If neither left or right is a superoperator,
                    # we should implicitly partial trace over
                    # matching dimensions of 1.
                    # Using izip_longest allows for the left and right dims
                    # to have uneven length (non-square Qobjs).
                    # We use None as padding so that it doesn't match anything,
                    # and will never cause a partial trace on the other side.
                    mask = [ll == r == 1 for ll, r in
                            zip_longest(dims[0], dims[1], fillvalue=None)]
                    # To ensure that there are still any dimensions left, we
                    # use max() to add a dimensions list of [1] if all matching dims
                    # are traced out of that side.
                    out.dims = [max([1],
                                    [dim for dim, m in zip(dims[0], mask)
                                     if not m]),
                                max([1],
                                    [dim for dim, m in zip(dims[1], mask)
                                     if not m])]

                else:
                    out.dims = dims

                out._isherm = None

                if self.superrep and other.superrep:
                    if self.superrep != other.superrep:
                        msg = ("Multiplying superoperators with different " +
                               "representations")
                        warnings.warn(msg)

                    out.superrep = self.superrep

                return out

            elif np.prod(self.shape) == 1:
                out = Qobj(other)
                out.data *= self.data[0, 0]
                out.superrep = other.superrep
                return out.tidyup() if auto_tidyup else out

            elif np.prod(other.shape) == 1:
                out = Qobj(self)
                out.data *= other.data[0, 0]
                out.superrep = self.superrep
                return out.tidyup() if auto_tidyup else out

            else:
                raise TypeError("Incompatible Qobj shapes")

        elif isinstance(other, np.ndarray):
            if other.dtype == 'object':
                return np.array([self * item for item in other],
                                dtype=object)
            else:
                return self.data * other

        elif isinstance(other, list):
            # if other is a list, do element-wise multiplication
            return np.array([self * item for item in other],
                            dtype=object)

        elif isinstance(other, (int, float, complex,
                                np.integer, np.floating, np.complexfloating)):
            out = Qobj()
            out.data = self.data * other
            out.dims = self.dims
            out.superrep = self.superrep
            if auto_tidyup:
                out.tidyup()
            if isinstance(other, complex):
                out._isherm = out.isherm
            else:
                out._isherm = self._isherm

            return out

        else:
            return NotImplemented

    def __rmul__(self, other):
        """
        MULTIPLICATION with Qobj on RIGHT [ ex. 4*Qobj ]
        """
        if isinstance(other, np.ndarray):
            if other.dtype == 'object':
                return np.array([item * self for item in other],
                                dtype=object)
            else:
                return other * self.data

        elif isinstance(other, list):
            # if other is a list, do element-wise multiplication
            return np.array([item * self for item in other],
                            dtype=object)

        elif isinstance(other, (int, float, complex,
                                np.integer, np.floating,
                                np.complexfloating)):
            out = Qobj()
            out.data = other * self.data
            out.dims = self.dims
            out.superrep = self.superrep
            if auto_tidyup:
                out.tidyup()
            if isinstance(other, complex):
                out._isherm = out.isherm
            else:
                out._isherm = self._isherm

            return out

        else:
            raise TypeError("Incompatible object for multiplication")

    def __truediv__(self, other):
        return self.__div__(other)

    def __div__(self, other):
        """
        DIVISION (by numbers only)
        """
        if isinstance(other, Qobj):  # if both are quantum objects
            raise TypeError("Incompatible Qobj shapes " +
                            "[division with Qobj not implemented]")

        if isinstance(other, (int, float, complex,
                              np.integer, np.floating, np.complexfloating)):
            out = Qobj()
            out.data = self.data / other
            out.dims = self.dims
            if auto_tidyup:
                out.tidyup()
            if isinstance(other, complex):
                out._isherm = out.isherm
            else:
                out._isherm = self._isherm

            out.superrep = self.superrep

            return out

        else:
            raise TypeError("Incompatible object for division")

    def __neg__(self):
        """
        NEGATION operation.
        """
        out = Qobj()
        out.data = -self.data
        out.dims = self.dims
        out.superrep = self.superrep
        if auto_tidyup:
            out.tidyup()
        out._isherm = self._isherm
        out._isunitary = self._isunitary
        return out

    def __getitem__(self, ind):
        """
        GET qobj elements.
        """
        out = self.data[ind]
        if sp.issparse(out):
            return np.asarray(out.todense())
        else:
            return out

    def __eq__(self, other):
        """
        EQUALITY operator.
        """
        return bool(isinstance(other, Qobj) and
                    self.dims == other.dims and
                    not np.any(np.abs((self.data - other.data).data) > atol))

    def __ne__(self, other):
        """
        INEQUALITY operator.
        """
        return not self == other

    def __pow__(self, n, m=None):  # calculates powers of Qobj
        """
        POWER operation.
        """
        if self.type not in ['oper', 'super']:
            raise Exception("Raising a qobj to some power works only for " +
                            "operators and super-operators (square matrices).")

        if m is not None:
            raise NotImplementedError("modulo is not implemented for Qobj")

        try:
            data = self.data ** n
            out = Qobj(data, dims=self.dims)
            out.superrep = self.superrep
            return out.tidyup() if auto_tidyup else out

        except ValueError:
            raise ValueError('Invalid choice of exponent.')

    def __abs__(self):
        return abs(self.data)

    def __str__(self):
        s = ""
        t = self.type
        shape = self.shape
        if self.type in ['oper', 'super']:
            s += ("Quantum object: " +
                  "dims = " + str(self.dims) +
                  ", shape = " + str(shape) +
                  ", type = " + t +
                  ", isherm = " + str(self.isherm) +
                  (
                      ", superrep = {0.superrep}".format(self)
                      if t == "super" and self.superrep != "super"
                      else ""
                  ) + "\n")
        else:
            s += ("Quantum object: " +
                  "dims = " + str(self.dims) +
                  ", shape = " + str(shape) +
                  ", type = " + t + "\n")
        s += "Qobj data =\n"

        if shape[0] > 10000 or shape[1] > 10000:
            # if the system is huge, don't attempt to convert to a
            # dense matrix and then to string, because it is pointless
            # and is likely going to produce memory errors. Instead print the
            # sparse data string representation
            s += str(self.data)

        elif all(np.imag(self.data.data) == 0):
            s += str(np.real(self.full()))

        else:
            s += str(self.full())

        return s

    def __repr__(self):
        # give complete information on Qobj without print statement in
        # command-line we cant realistically serialize a Qobj into a string,
        # so we simply return the informal __str__ representation instead.)
        return self.__str__()

    def __call__(self, other):
        """
        Acts this Qobj on another Qobj either by left-multiplication,
        or by vectorization and devectorization, as
        appropriate.
        """
        if not isinstance(other, Qobj):
            raise TypeError("Only defined for quantum objects.")

        if self.type == "oper":
            if other.type == "ket":
                return self * other
            else:
                raise TypeError("Can only act oper on ket.")
        else:
            return None

    def __getstate__(self):
        # defines what happens when Qobj object gets pickled
        self.__dict__.update({'qiskit_version': __version__[:5]})
        return self.__dict__

    def __setstate__(self, state):
        # defines what happens when loading a pickled Qobj
        if 'qiskit_version' in state.keys():
            del state['qiskit_version']
        (self.__dict__).update(state)

    def _repr_latex_(self):
        """
        Generate a LaTeX representation of the Qobj instance. Can be used for
        formatted output in ipython notebook.
        """
        t = self.type
        shape = self.shape
        s = r''
        if self.type in ['oper', 'super']:
            s += ("Quantum object: " +
                  "dims = " + str(self.dims) +
                  ", shape = " + str(shape) +
                  ", type = " + t +
                  ", isherm = " + str(self.isherm) +
                  (
                      ", superrep = {0.superrep}".format(self)
                      if t == "super" and self.superrep != "super"
                      else ""
                  ))
        else:
            s += ("Quantum object: " +
                  "dims = " + str(self.dims) +
                  ", shape = " + str(shape) +
                  ", type = " + t)

        M, N = self.data.shape

        s += r'\begin{equation*}\left(\begin{array}{*{11}c}'

        def _format_float(value):
            if value == 0.0:
                return "0.0"
            elif abs(value) > 1000.0 or abs(value) < 0.001:
                return ("%.3e" % value).replace("e", r"\times10^{") + "}"
            elif abs(value - int(value)) < 0.001:
                return "%.1f" % value
            else:
                return "%.3f" % value

        def _format_element(_, n, d):
            s = " & " if n > 0 else ""
            if isinstance(d, str):
                return s + d
            else:
                if abs(np.imag(d)) < atol:
                    return s + _format_float(np.real(d))
                elif abs(np.real(d)) < atol:
                    return s + _format_float(np.imag(d)) + "j"
                else:
                    s_re = _format_float(np.real(d))
                    s_im = _format_float(np.imag(d))
                    if np.imag(d) > 0.0:
                        return s + "(" + s_re + "+" + s_im + "j)"
                    else:
                        return s + "(" + s_re + s_im + "j)"

        if M > 10 and N > 10:
            # truncated matrix output
            for m in range(5):
                for n in range(5):
                    s += _format_element(m, n, self.data[m, n])
                s += r' & \cdots'
                for n in range(N - 5, N):
                    s += _format_element(m, n, self.data[m, n])
                s += r'\\'

            for n in range(5):
                s += _format_element(m, n, r'\vdots')
            s += r' & \ddots'
            for n in range(N - 5, N):
                s += _format_element(m, n, r'\vdots')
            s += r'\\'

            for m in range(M - 5, M):
                for n in range(5):
                    s += _format_element(m, n, self.data[m, n])
                s += r' & \cdots'
                for n in range(N - 5, N):
                    s += _format_element(m, n, self.data[m, n])
                s += r'\\'

        elif N <= 10 < M:
            # truncated vertically elongated matrix output
            for m in range(5):
                for n in range(N):
                    s += _format_element(m, n, self.data[m, n])
                s += r'\\'

            for n in range(N):
                s += _format_element(m, n, r'\vdots')
            s += r'\\'

            for m in range(M - 5, M):
                for n in range(N):
                    s += _format_element(m, n, self.data[m, n])
                s += r'\\'

        elif M <= 10 < N:
            # truncated horizontally elongated matrix output
            for m in range(M):
                for n in range(5):
                    s += _format_element(m, n, self.data[m, n])
                s += r' & \cdots'
                for n in range(N - 5, N):
                    s += _format_element(m, n, self.data[m, n])
                s += r'\\'

        else:
            # full output
            for m in range(M):
                for n in range(N):
                    s += _format_element(m, n, self.data[m, n])
                s += r'\\'

        s += r'\end{array}\right)\end{equation*}'
        return s

    def dag(self):
        """Adjoint operator of quantum object.
        """
        out = Qobj()
        out.data = zcsr_adjoint(self.data)
        out.dims = [self.dims[1], self.dims[0]]
        out._isherm = self._isherm
        out.superrep = self.superrep
        return out

    def conj(self):
        """Conjugate operator of quantum object.
        """
        out = Qobj()
        out.data = self.data.conj()
        out.dims = [self.dims[0], self.dims[1]]
        return out

    def norm(self, norm=None, sparse=False, tol=0, maxiter=100000):
        """Norm of a quantum object.

        Default norm is L2-norm for kets and trace-norm for operators.
        Other ket and operator norms may be specified using the `norm` and
        argument.

        Args:
            norm (str): Which norm to use for ket/bra vectors: L2 'l2',
                        max norm 'max', or for operators: trace 'tr', Frobius
                        'fro', one 'one', or max 'max'.

            sparse (bool): Use sparse eigenvalue solver for trace norm.
                           Other norms are not affected by this parameter.

            tol (float): Tolerance for sparse solver (if used) for trace norm.
                         The sparse solver may not converge if the tolerance
                         is set too low.

            maxiter (int): Maximum number of iterations performed by sparse
                           solver (if used) for trace norm.

        Returns:
            float: The requested norm of the operator or state quantum object.

        Raises:
            ValueError: Invalid input.
        """
        if self.type in ['oper', 'super']:
            if norm is None or norm == 'tr':
                _op = self * self.dag()
                vals = sp_eigs(_op.data, _op.isherm, vecs=False,
                               sparse=sparse, tol=tol, maxiter=maxiter)
                return np.sum(np.sqrt(np.abs(vals)))
            elif norm == 'fro':
                return sp_fro_norm(self.data)
            elif norm == 'one':
                return sp_one_norm(self.data)
            elif norm == 'max':
                return sp_max_norm(self.data)
            else:
                raise ValueError(
                    "For matrices, norm must be 'tr', 'fro', 'one', or 'max'.")
        else:
            if norm is None or norm == 'l2':
                return sp_L2_norm(self.data)
            elif norm == 'max':
                return sp_max_norm(self.data)
            else:
                raise ValueError("For vectors, norm must be 'l2', or 'max'.")

    def proj(self):
        """Form the projector from a given ket or bra vector.

        Returns:
            qobj.Qobj: Projection operator.
        Raises:
            TypeError: Project from only bra or ket.
        """
        if self.isket:
            _out = zcsr_proj(self.data, 1)
            _dims = [self.dims[0], self.dims[0]]
        elif self.isbra:
            _out = zcsr_proj(self.data, 0)
            _dims = [self.dims[1], self.dims[1]]
        else:
            raise TypeError('Projector can only be formed from a bra or ket.')

        return Qobj(_out, dims=_dims)

    def tr(self):
        """Trace of a quantum object.

        Returns
        -------
        trace : float
            Returns ``real`` if operator is Hermitian, returns ``complex``
            otherwise.

        """
        return zcsr_trace(self.data, self.isherm)

    def full(self, order='C', squeeze=False):
        """Dense array from quantum object.

        Parameters
        ----------
        order : str {'C', 'F'}
            Return array in C (default) or Fortran ordering.
        squeeze : bool {False, True}
            Squeeze output array.

        Returns
        -------
        data : array
            Array of complex data from quantum objects `data` attribute.
        """
        if squeeze:
            return self.data.toarray(order=order).squeeze()
        else:
            return self.data.toarray(order=order)

    # pylint: disable=unused-argument
    def __array__(self, *arg, **kwarg):
        """Numpy array from Qobj
        For compatibility with np.array
        """
        return self.full()

    def diag(self):
        """Diagonal elements of quantum object.

        Returns
        -------
        diags : array
            Returns array of ``real`` values if operators is Hermitian,
            otherwise ``complex`` values are returned.

        """
        out = self.data.diagonal()
        if np.any(np.imag(out) > atol) or not self.isherm:
            return out
        else:
            return np.real(out)

    def expm(self, method='dense'):
        """Matrix exponential of quantum operator.

        Input operator must be square.

        Args:
            method (str): Use set method to use to calculate the matrix
                          exponentiation. The available choices includes
                          'dense' and 'sparse'.  Since the exponential of
                          a matrix is nearly always dense, method='dense'
                          is set as default.
        Returns:
            Qobj: Exponentiated quantum operator.

        Raises:
            TypeError: Quantum operator is not square.
            ValueError: Invalid input.

        """
        if self.dims[0][0] != self.dims[1][0]:
            raise TypeError('Invalid operand for matrix exponential')

        if method == 'dense':
            F = sp_expm(self.data, sparse=False)

        elif method == 'sparse':
            F = sp_expm(self.data, sparse=True)

        else:
            raise ValueError("method must be 'dense' or 'sparse'.")

        out = Qobj(F, dims=self.dims)
        return out.tidyup() if auto_tidyup else out

    def check_herm(self):
        """Check if the quantum object is hermitian.

        Returns:
            bool: Returns the new value of isherm property.
        """
        self._isherm = None
        return self.isherm

    def sqrtm(self, sparse=False, tol=0, maxiter=100000):
        """Sqrt of a quantum operator.

        Operator must be square.

        Args:
            sparse (bool): Use sparse eigenvalue/vector solver.

            tol (float): Tolerance used by sparse solver
                         (0 = machine precision).

            maxiter (int): Maximum number of iterations used by
                           sparse solver.

        Returns:
            Qobj: Matrix square root of operator.

        Raises:
            TypeError: Quantum object is not square.
        """
        if self.dims[0][0] == self.dims[1][0]:
            evals, evecs = sp_eigs(self.data, self.isherm, sparse=sparse,
                                   tol=tol, maxiter=maxiter)
            numevals = len(evals)
            dV = sp.spdiags(np.sqrt(evals, dtype=complex), 0, numevals,
                            numevals, format='csr')
            if self.isherm:
                spDv = dV.dot(evecs.T.conj().T)
            else:
                spDv = dV.dot(np.linalg.inv(evecs.T))

            out = Qobj(evecs.T.dot(spDv), dims=self.dims)
            return out.tidyup() if auto_tidyup else out

        else:
            raise TypeError('Invalid operand for matrix square root')

    def cosm(self):
        """Cosine of a quantum operator.

        Operator must be square.

        Returns
        -------
        oper : :class:`qutip.Qobj`
            Matrix cosine of operator.

        Raises
        ------
        TypeError
            Quantum object is not square.

        Notes
        -----
        Uses the Q.expm() method.

        """
        if self.dims[0][0] == self.dims[1][0]:
            return 0.5 * ((1j * self).expm() + (-1j * self).expm())
        else:
            raise TypeError('Invalid operand for matrix square root')

    def sinm(self):
        """Sine of a quantum operator.

        Operator must be square.

        Returns
        -------
        oper : :class:`qutip.Qobj`
            Matrix sine of operator.

        Raises
        ------
        TypeError
            Quantum object is not square.

        Notes
        -----
        Uses the Q.expm() method.

        """
        if self.dims[0][0] == self.dims[1][0]:
            return -0.5j * ((1j * self).expm() - (-1j * self).expm())

        raise TypeError('Invalid operand for matrix square root')

    def unit(self, inplace=False,
             norm=None, sparse=False,
             tol=0, maxiter=100000):
        """Operator or state normalized to unity.

        Uses norm from Qobj.norm().

        Args:
            inplace (bool): Do an in-place normalization
            norm (str): Requested norm for states / operators.
            sparse (bool): Use sparse eigensolver for trace norm.
            Does not affect other norms.
            tol (float): Tolerance used by sparse eigensolver.
            maxiter (int): Number of maximum iterations performed by
            sparse eigensolver.

        Returns:
            qobj.Qobj: Normalized quantum object if not in-place, else None.

        Raises:
            TypeError: Inplace value must be a bool.
        """
        if inplace:
            nrm = self.norm(norm=norm, sparse=sparse,
                            tol=tol, maxiter=maxiter)

            self.data /= nrm

            return None
        elif not inplace:
            out = self / self.norm(norm=norm, sparse=sparse,
                                   tol=tol, maxiter=maxiter)
            if auto_tidyup:
                return out.tidyup()
            else:
                return out
        else:
            raise TypeError('inplace kwarg must be bool.')

    def tidyup(self, atol=auto_tidyup_atol):
        """Removes small elements from the quantum object.

        Parameters
        ----------
        atol : float
            Absolute tolerance used by tidyup. Default is set
            via qutip global settings parameters.

        Returns
        -------
        oper : :class:`qutip.Qobj`
            Quantum object with small elements removed.

        """
        if self.data.nnz:
            # This does the tidyup and returns True if
            # The sparse data needs to be shortened
            if cy_tidyup(self.data.data, atol, self.data.nnz):
                self.data.eliminate_zeros()
            return self
        else:
            return self

    def transform(self, inpt, inverse=False, sparse=True):
        """Basis transform defined by input array.

        Input array can be a ``matrix`` defining the transformation,
        or a ``list`` of kets that defines the new basis.

        Args:
            inpt (ndarray): A ``matrix`` or ``list`` of kets defining
                            the transformation.
            inverse (bool): Whether to return inverse transformation.

            sparse (bool): Use sparse matrices when possible. Can be slower.

        Returns:
            Qobj: Operator in new basis.

        Raises:
            TypeError: Invalid input.

        """
        if isinstance(inpt, list) or (isinstance(inpt, np.ndarray) and
                                      len(inpt.shape) == 1):
            if len(inpt) != max(self.shape):
                raise TypeError(
                    'Invalid size of ket list for basis transformation')
            if sparse:
                S = sp.hstack([psi.data for psi in inpt], format='csr').conj().T
            else:
                S = np.hstack([psi.full() for psi in inpt]).conj().T
        elif isinstance(inpt, Qobj) and inpt.isoper:
            S = inpt.data
        elif isinstance(inpt, np.ndarray):
            S = inpt.conj()
            sparse = False
        else:
            raise TypeError('Invalid operand for basis transformation')

        # transform data
        if inverse:
            if self.isket:
                data = (S.conj().T) * self.data
            elif self.isbra:
                data = self.data.dot(S)
            else:
                if sparse:
                    data = (S.conj().T) * self.data * S
                else:
                    data = (S.conj().T).dot(self.data.dot(S))
        else:
            if self.isket:
                data = S * self.data
            elif self.isbra:
                data = self.data.dot(S.conj().T)
            else:
                if sparse:
                    data = S * self.data * (S.conj().T)
                else:
                    data = S.dot(self.data.dot(S.conj().T))

        out = Qobj(data, dims=self.dims)
        out._isherm = self._isherm
        out.superrep = self.superrep

        if auto_tidyup:
            return out.tidyup()
        else:
            return out

    def matrix_element(self, bra, ket):
        """Calculates a matrix element.

        Gives the matrix element for the quantum object sandwiched between a
        `bra` and `ket` vector.

        Args:
            bra (Qobj): Quantum object of type 'bra' or 'ket'

            ket (Qobj): Quantum object of type 'ket'.

        Returns:
            complex: Complex valued matrix element.

        Raises:
            TypeError: Invalid input.

        """
        if not self.isoper:
            raise TypeError("Can only get matrix elements for an operator.")

        if bra.isbra and ket.isket:
            return zcsr_mat_elem(self.data, bra.data, ket.data, 1)

        elif bra.isket and ket.isket:
            return zcsr_mat_elem(self.data, bra.data, ket.data, 0)
        else:
            raise TypeError("Can only calculate matrix elements " +
                            "for bra and ket vectors.")

    def overlap(self, other):
        """Overlap between two state vectors or two operators.

        Gives the overlap (inner product) between the current bra or ket Qobj
        and and another bra or ket Qobj. It gives the Hilbert-Schmidt overlap
        when one of the Qobj is an operator/density matrix.

        Parameters
        -----------
        other : :class:`qutip.Qobj`
            Quantum object for a state vector of type 'ket', 'bra' or density
            matrix.

        Returns
        -------
        overlap : complex
            Complex valued overlap.

        Raises
        ------
        TypeError
            Can only calculate overlap between a bra, ket and density matrix
            quantum objects.

        Notes
        -----
        Since QuTiP mainly deals with ket vectors, the most efficient inner
        product call is the ket-ket version that computes the product
        <self|other> with both vectors expressed as kets.
        """

        if isinstance(other, Qobj):

            returnval = 0

            if self.isbra:
                if other.isket:
                    returnval = zcsr_inner(self.data, other.data, 1)
                elif other.isbra:
                    # Since we deal mainly with ket vectors, the bra-bra combo
                    # is not common, and not optimized.
                    returnval = zcsr_inner(self.data, other.dag().data, 1)
                elif other.isoper:
                    returnval = (states.ket2dm(self).dag() * other).tr()
                else:
                    raise TypeError("Can only calculate overlap for " +
                                    "state vector Qobjs")

            elif self.isket:
                if other.isbra:
                    returnval = zcsr_inner(other.data, self.data, 1)
                elif other.isket:
                    returnval = zcsr_inner(self.data, other.data, 0)
                elif other.isoper:
                    returnval = (states.ket2dm(self).dag() * other).tr()
                else:
                    raise TypeError("Can only calculate overlap for " +
                                    "state vector Qobjs")

            elif self.isoper:
                if other.isket or other.isbra:
                    returnval = (self.dag() * states.ket2dm(other)).tr()
                elif other.isoper:
                    returnval = (self.dag() * other).tr()
                else:
                    raise TypeError("Can only calculate overlap " +
                                    "for state vector Qobjs")
        else:
            raise TypeError("Can only calculate overlap for state vector Qobjs")

        return returnval

    def eigenstates(self, sparse=False, sort='low',
                    eigvals=0, tol=0, maxiter=100000):
        """Eigenstates and eigenenergies.

        Eigenstates and eigenenergies are defined for operators and
        superoperators only.

        Parameters
        ----------
        sparse : bool
            Use sparse Eigensolver

        sort : str
            Sort eigenvalues (and vectors) 'low' to high, or 'high' to low.

        eigvals : int
            Number of requested eigenvalues. Default is all eigenvalues.

        tol : float
            Tolerance used by sparse Eigensolver (0 = machine precision).
            The sparse solver may not converge if the tolerance is set too low.

        maxiter : int
            Maximum number of iterations performed by sparse solver (if used).

        Returns
        -------
        eigvals : array
            Array of eigenvalues for operator.

        eigvecs : array
            Array of quantum operators representing the oprator eigenkets.
            Order of eigenkets is determined by order of eigenvalues.

        Notes
        -----
        The sparse eigensolver is much slower than the dense version.
        Use sparse only if memory requirements demand it.

        """
        evals, evecs = sp_eigs(self.data, self.isherm, sparse=sparse,
                               sort=sort, eigvals=eigvals, tol=tol,
                               maxiter=maxiter)
        new_dims = [self.dims[0], [1] * len(self.dims[0])]
        ekets = np.array([Qobj(vec, dims=new_dims) for vec in evecs],
                         dtype=object)
        norms = np.array([ket.norm() for ket in ekets])
        return evals, ekets / norms

    def eigenenergies(self, sparse=False, sort='low',
                      eigvals=0, tol=0, maxiter=100000):
        """Eigenenergies of a quantum object.
        Eigenenergies (eigenvalues) are defined for operators or superoperators
        only.

        Parameters
        ----------
        sparse : bool
            Use sparse Eigensolver
        sort : str
            Sort eigenvalues 'low' to high, or 'high' to low.
        eigvals : int
            Number of requested eigenvalues. Default is all eigenvalues.
        tol : float
            Tolerance used by sparse Eigensolver (0=machine precision).
            The sparse solver may not converge if the tolerance is set too low.
        maxiter : int
            Maximum number of iterations performed by sparse solver (if used).

        Returns
        -------
        eigvals : array
            Array of eigenvalues for operator.

        Notes
        -----
        The sparse eigensolver is much slower than the dense version.
        Use sparse only if memory requirements demand it.

        """
        return sp_eigs(self.data, self.isherm, vecs=False, sparse=sparse,
                       sort=sort, eigvals=eigvals, tol=tol, maxiter=maxiter)

    def groundstate(self, sparse=False, tol=0, maxiter=100000, safe=True):
        """Ground state Eigenvalue and Eigenvector.

        Defined for quantum operators or superoperators only.

        Args:
            sparse (bool): Use sparse Eigensolver

            tol (float): Tolerance used by sparse Eigensolver
                         (0 = machine precision). The sparse solver
                         may not converge if the tolerance is set too low.

            maxiter (int): Maximum number of iterations performed by
                           sparse solver (if used).

            safe (bool): Check for degenerate ground state

        Returns:
            tuple: Eigenenergy and eigenstate of ground state.

        """
        if safe:
            evals = 2
        else:
            evals = 1
        grndval, grndvec = sp_eigs(self.data, self.isherm, sparse=sparse,
                                   eigvals=evals, tol=tol, maxiter=maxiter)
        if safe:
            if tol == 0:
                tol = 1e-15
            if (grndval[1] - grndval[0]) <= 10 * tol:
                print("WARNING: Ground state may be degenerate. "
                      "Use Q.eigenstates()")
        new_dims = [self.dims[0], [1] * len(self.dims[0])]
        grndvec = Qobj(grndvec[0], dims=new_dims)
        grndvec = grndvec / grndvec.norm()
        return grndval[0], grndvec

    def trans(self):
        """Transposed operator.

        Returns:
            Qobj: Transpose of input operator.

        """
        out = Qobj()
        out.data = zcsr_transpose(self.data)
        out.dims = [self.dims[1], self.dims[0]]
        return out

    @property
    def isherm(self):
        """Is operator Hermitian.

        Returns:
            bool: Operator is Hermitian or not.
        """

        if self._isherm is not None:
            # used previously computed value
            return self._isherm

        self._isherm = bool(zcsr_isherm(self.data))

        return self._isherm

    @isherm.setter
    def isherm(self, isherm):
        self._isherm = isherm

    def check_isunitary(self):
        """
        Checks whether qobj is a unitary matrix
        """
        if self.isoper:
            eye_data = fast_identity(self.shape[0])
            return not (np.any(np.abs((self.data * self.dag().data -
                                       eye_data).data) > atol) or
                        np.any(np.abs((self.dag().data * self.data -
                                       eye_data).data) > atol))

        else:
            return False

    @property
    def isunitary(self):
        """Is operator unitary.

        Returns:
            bool: Is operator unitary or not.
        """
        if self._isunitary is not None:
            # used previously computed value
            return self._isunitary

        self._isunitary = self.check_isunitary()

        return self._isunitary

    @isunitary.setter
    def isunitary(self, isunitary):
        self._isunitary = isunitary

    @property
    def type(self):
        """Type of Qobj
        """
        if not self._type:
            self._type = type_from_dims(self.dims)

        return self._type

    @property
    def shape(self):
        """Shape of Qobj
        """
        if self.data.shape == (1, 1):
            return tuple([np.prod(self.dims[0]), np.prod(self.dims[1])])
        else:
            return tuple(self.data.shape)

    @property
    def isbra(self):
        """Is bra vector"""
        return self.type == 'bra'

    @property
    def isket(self):
        """Is ket vector"""
        return self.type == 'ket'

    @property
    def isoperbra(self):
        """Is operator-bra"""
        return self.type == 'operator-bra'

    @property
    def isoperket(self):
        """Is operator-ket"""
        return self.type == 'operator-ket'

    @property
    def isoper(self):
        """Is operator"""
        return self.type == 'oper'

    @property
    def issuper(self):
        """Is super operator"""
        return self.type == 'super'

    @staticmethod
    def evaluate(qobj_list, t, args):
        """Evaluate a time-dependent quantum object in list format. For
        example,

            qobj_list = [H0, [H1, func_t]]

        is evaluated to

            Qobj(t) = H0 + H1 * func_t(t, args)

        and

            qobj_list = [H0, [H1, 'sin(w * t)']]

        is evaluated to

            Qobj(t) = H0 + H1 * sin(args['w'] * t)

        Args:
            qobj_list (list): A nested list of Qobj instances and
                              corresponding time-dependent coefficients.

            t (float): The time for which to evaluate the time-dependent
                       Qobj instance.

            args (dict): A dictionary with parameter values required
                         to evaluate the time-dependent Qobj intance.

        Returns:
            Qobj: A Qobj instance that represents the value of qobj_list
                  at time t.

        Raises:
            TypeError: Invalid input.

        """
        q_sum = 0
        if isinstance(qobj_list, Qobj):
            q_sum = qobj_list
        elif isinstance(qobj_list, list):
            for q in qobj_list:
                if isinstance(q, Qobj):
                    q_sum += q
                elif (isinstance(q, list) and len(q) == 2 and
                      isinstance(q[0], Qobj)):
                    if isinstance(q[1], types.FunctionType):
                        q_sum += q[0] * q[1](t, args)
                    elif isinstance(q[1], str):
                        args['t'] = t
                        # pylint: disable=eval-used
                        q_sum += q[0] * float(eval(q[1], globals(), args))
                    else:
                        raise TypeError('Unrecognized format for ' +
                                        'specification of time-dependent Qobj')
                else:
                    raise TypeError('Unrecognized format for specification ' +
                                    'of time-dependent Qobj')
        else:
            raise TypeError(
                'Unrecongized format for specification of time-dependent Qobj')

        return q_sum


# pylint: disable=wrong-import-position
from ..qutip_lite import states
