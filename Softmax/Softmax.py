"""
    Linear Softmax Classifier.
 """
import sys
sys.path.append('..')

import numpy as np
import utils as ut

def cross_entropy_loss(data, labels, weights, reg_lambda):
    """
        Calculates cross entropy loss.

        Parameters:
        -------
        data : np.array, where each row is a sample
        labels : np.array, where each element is a label for a sample
        weights : np.array, weight matrix for cost function
        margin : int, margin for loss calcs
        reg_lambda : float, regularization koef

        Returns:
            Loss = cross_entropy_loss + reg_loss.
    """
    response = np.dot(data, weights)
    maxs = np.amax(response, axis=1, keepdims=True)
    response -= maxs
    response = np.exp(response)
    response = response / np.sum(response, axis=1, keepdims=True)
    corect_responses = -np.log(response[range(data.shape[0]), labels])

    reg_loss = 0.5 * reg_lambda * np.sum(weights ** 2)
    return np.sum(corect_responses) / data.shape[0] + reg_loss

def cross_entropy_loss_gradient(data, labels, weights, reg_lambda):
    """
        Analitic calculation of the cross_entropy_loss gradient.

        Parameters:
        -------
        data : np.array, where each row is a sample
        labels : np.array, where each element is a label for a sample
        weights : np.array, weight matrix for cost function
        margin : int, margin for loss calcs
        reg_lambda : float, regularization koef

        Returns:
            Gradient vector
    """
    response = np.dot(data, weights)
    maxs = np.amax(response, axis=1, keepdims=True)
    response -= maxs
    response = np.exp(response)
    response = response / np.sum(response, axis=1, keepdims=True)

    response[range(data.shape[0]), labels] -= 1
    response /= data.shape[0]

    reg_loss = reg_lambda * np.sum(weights)
    return np.dot(data.T, response) + reg_loss


class SoftmaxClassifier(object):
    """
        Softmax classifier.
    """
    def __init__(self, learning_rate=0.01, reg_lambda=0.01, batch_size=1024):
        self.reg_lambda = reg_lambda
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.weights = np.array([])

    def train(self, data, labels, max_iters=1000):
        """
            Train Softmax classifier.

            Parameters:
            -------
            data : np.array, where each row is data sample
            labels: np.array, where each element is sample labels
            max_iters: max count of iterations for training
        """
        classes_count = len(np.unique(labels))
        self.weights = 0.01 * np.random.randn(data.shape[1] + 1, classes_count)

        for i in xrange(max_iters):
            cur_batch_size = min(self.batch_size, data.shape[0])
            rand_idxs = [np.random.randint(0, data.shape[0]) for _ in xrange(cur_batch_size)]

            ones = np.ones((cur_batch_size, 1))
            data_batch = data[rand_idxs]
            data_batch = np.hstack((data_batch, ones))
            labels_batch = labels[rand_idxs]

            # Numerical
            # gradient = ut.compute_gradient(lambda x: cross_entropy_loss(data_batch,
            #                                                             labels_batch, x,
            #                                                             self.reg_lambda),
            #                                self.weights)

            # Analitic
            gradient = cross_entropy_loss_gradient(data_batch, labels_batch,
                                                   self.weights, self.reg_lambda)
            self.weights += -self.learning_rate * gradient

    def predict(self, data):
        """
            Predict labels for data.

            Parameters:
            -------
            data : np.array, where each row is data sample

            Returns:
            labels : np.array, where each element it's a label for sample from data.
        """
        ones = np.ones((data.shape[0], 1))
        data = np.hstack((data, ones))
        response = np.dot(data, self.weights)
        response = np.argmax(response, axis=1)

        return response
 