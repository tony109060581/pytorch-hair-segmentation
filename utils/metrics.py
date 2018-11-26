import torch
from ignite.metrics.metric import Metric


class Accuracy(Metric):
    """
    Calculates the accuracy.

    - `update` must receive output of the form `(y_pred, y)`.
    - `y_pred` must be in the following shape (batch_size, num_categories, ...) or (batch_size, ...)
    - `y` must be in the following shape (batch_size, ...)
    """
    def reset(self):
        self._num_correct = 0
        self._num_examples = 0

    def update(self, output):
        y_pred, y = output
        y = y.long()

        if not (y.ndimension() == y_pred.ndimension() or y.ndimension() + 1 == y_pred.ndimension()):
            raise ValueError("y must have shape of (batch_size, ...) and y_pred "
                             "must have shape of (batch_size, num_classes, ...) or (batch_size, ...).")

        if y.ndimension() > 1 and y.shape[1] == 1:
            y = y.squeeze(dim=1)

        if y_pred.ndimension() > 1 and y_pred.shape[1] == 1:
            y_pred = y_pred.squeeze(dim=1)

        y_shape = y.shape
        y_pred_shape = y_pred.shape

        if y.ndimension() + 1 == y_pred.ndimension():
            y_pred_shape = (y_pred_shape[0], ) + y_pred_shape[2:]

        if not (y_shape == y_pred_shape):
            raise ValueError("y and y_pred must have compatible shapes.")

        if y_pred.ndimension() == y.ndimension():
            # Maps Binary Case to Categorical Case with 2 classes
            y_pred = y_pred.unsqueeze(dim=1)
            y_pred = torch.cat([1.0 - y_pred, y_pred], dim=1)

        indices = torch.max(y_pred, dim=1)[1]
        correct = torch.eq(indices, y).view(-1)

        self._num_correct += torch.sum(correct).item()
        self._num_examples += correct.shape[0]

    def compute(self):
        if self._num_examples == 0:
            raise ValueError('Accuracy must have at least one example before it can be computed')
        return self._num_correct / self._num_examples


class MeanIU(Metric):
    def __init__(self, thrs):
        super(MeanIU, self).__init__()
        self.thrs = thrs
        self._num_intersect = 0
        self._num_union = 0

    def reset(self):
        self._num_intersect = 0
        self._num_union = 0

    def update(self, output):
        y_pred, y = output

        y_pred = torch.sigmoid(y_pred) >= self.thrs
        y = y.byte()

        intersect = y_pred * y == 1
        union = y_pred + y > 0

        self._num_intersect = torch.sum(intersect).item()
        self._num_union = torch.sum(union).item()


    def compute(self):
        if self._num_union == 0:
            raise ValueError('MeanIU must have at least one example before it can be computed')
        return self._num_intersect / self._num_union
