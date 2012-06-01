######################
# (c) 2012 Andreas Mueller <amueller@ais.uni-bonn.de>
# License: BSD 3-clause
#
# Implements structured SVM as described in Tsochantaridis et. al.
# Support Vector Machines Learning for Interdependend
# and Structures Output Spaces

import numpy as np
import cvxopt
import cvxopt.solvers
import matplotlib.pyplot as plt

from IPython.core.debugger import Tracer

#cvxopt.solvers.options['show_progress'] = False
tracer = Tracer()


class StructuredSVM(object):
    """Margin rescaled with l1 slack penalty."""
    def __init__(self, problem, max_iter=100, C=1.0):
        self.max_iter = max_iter
        self.problem = problem
        self.C = float(C)
        self.initvals = dict()

    def _solve_qp(self, constraints, psis, losses):
        psi_matrix = np.vstack(psis)
        n_constraints = len(constraints)
        P = cvxopt.matrix(np.dot(psi_matrix, psi_matrix.T))
        q = cvxopt.matrix(-np.array(losses, dtype=np.float))
        idy = np.identity(n_constraints)
        G = cvxopt.matrix(np.vstack((-idy, idy)))
        tmp1 = np.zeros(n_constraints)
        tmp2 = np.ones(n_constraints) * self.C
        h = cvxopt.matrix(np.hstack((tmp1, tmp2)))
        # solve QP problem
        solution = cvxopt.solvers.qp(P, q, G, h, initvals=self.initvals)

        # Lagrange multipliers
        a = np.ravel(solution['x'])

        # Support vectors have non zero lagrange multipliers
        sv = a > 1e-5
        print("%d support vectors out of %d points" % (np.sum(sv),
            n_constraints))
        print("Coefficients at C: %d" % np.sum(self.C - a < 1e-3))
        w = np.zeros(self.problem.size_psi)
        for issv, dpsi, alpha in zip(sv, psis, a):
            if not issv:
                continue
            w += alpha * dpsi
        return w

    def fit(self, X, Y):
        psi = self.problem.psi
        w = np.zeros(self.problem.size_psi)
        constraints = []
        psis = []
        losses = []
        for iteration in xrange(self.max_iter):
            print("iteration %d" % iteration)
            new_constraints = 0
            current_loss = 0.
            for i, x, y in zip(np.arange(len(X)), X, Y):
                y_hat = self.problem.loss_augmented_inference(x, y, w)
                loss = self.problem.loss(y, y_hat)
                constraint = np.str((i, y, y_hat))
                if loss and not constraints.count(constraint):
                    constraints.append(constraint)
                    delta_psi = psi(x, y) - psi(x, y_hat)
                    psis.append(delta_psi / 1000.)
                    losses.append(loss)
                    current_loss += loss
                    new_constraints += 1
            if new_constraints == 0:
                print("no loss on training set")
                break
            print("current loss: %f  new constraints: %d" %
                    (current_loss / len(X), new_constraints))
            w = self._solve_qp(constraints, psis, losses)

            print(w)
        self.w = w

    def predict(self, X):
        prediction = []
        for x in X:
            prediction.append(self.problem.inference(x, self.w))
        return prediction


class LatentStructuredSVM(StructuredSVM):
    """Margin rescaled with l1 slack penalty."""
    def _solve_qp(self, constraints, psis, losses):
        psi_matrix = np.vstack(psis)
        n_constraints = len(constraints)
        P = cvxopt.matrix(np.dot(psi_matrix, psi_matrix.T))
        q = cvxopt.matrix(-np.array(losses, dtype=np.float))
        idy = np.identity(n_constraints)
        G = cvxopt.matrix(np.vstack((-idy, idy)))
        tmp1 = np.zeros(n_constraints)
        tmp2 = np.ones(n_constraints) * self.C
        h = cvxopt.matrix(np.hstack((tmp1, tmp2)))
        # solve QP problem
        solution = cvxopt.solvers.qp(P, q, G, h)

        # Lagrange multipliers
        a = np.ravel(solution['x'])

        # Support vectors have non zero lagrange multipliers
        sv = a > 1e-5
        print("%d support vectors out of %d points" % (np.sum(sv),
            n_constraints))
        print("Coefficients at C: %d" % np.sum(self.C - a < 1e-3))
        w = np.zeros(self.problem.size_psi)
        for issv, dpsi, alpha in zip(sv, psis, a):
            if not issv:
                continue
            w += alpha * dpsi
        return w

    def fit(self, X, Y):
        psi = self.problem.psi
        w = np.zeros(self.problem.size_psi)
        constraints = []
        psis = []
        losses = []
        for iteration in xrange(self.max_iter):
            print("iteration %d" % iteration)
            new_constraints = 0
            current_loss = 0.
            for i, x, y in zip(np.arange(len(X)), X, Y):
                h = self.problem.latent(x, y, w)
                h_hat, y_hat = self.problem.loss_augmented_inference(x, y, w)
                plt.matshow(h.reshape(18, 18))
                #plt.savefig("figures/h_%03d_%03d.png" % (iteration, i))
                plt.savefig("h_%03d_%03d.png" % (iteration, i))
                plt.close()
                h_hat, y_hat = self.problem.inference(x, w)
                plt.matshow(h_hat.reshape(18, 18))
                #plt.savefig("figures/h_hat_%03d_%03d.png" % (iteration, i))
                plt.savefig("h_hat_%03d_%03d.png" % (iteration, i))
                plt.close()
                loss = self.problem.loss(y, y_hat)
                constraint = np.str((x, h, y, h_hat, y_hat))
                if loss and not constraints.count(constraint):
                    constraints.append(constraint)
                    delta_psi = psi(x, h, y) - psi(x, h_hat, y_hat)
                    psis.append(delta_psi / 1000.)
                    losses.append(loss)
                    current_loss += loss
                    new_constraints += 1
            if new_constraints == 0:
                print("no loss on training set")
                break
            print("current loss: %f  new constraints: %d" %
                    (current_loss / len(X), new_constraints))
            w = self._solve_qp(constraints, psis, losses)

            print(w)
        self.w = w
        tracer()

    def predict(self, X):
        prediction = []
        for x in X:
            prediction.append(self.problem.inference(x, self.w)[0])
        return prediction
