import os
import cv2
import numpy as np
import tensorflow as tf

from utils import inv_transform, cal_mae, cal_me, cal_mse, cal_pcc

class Solver(object):
    def __init__(self, sess, model):
        self.sess = sess
        self.model = model

        # self.dataset = Dataset(self.flags.dataset)

    def train(self, x, y):
        feed = {
            self.model.x: x,
            self.model.y: y,
            self.model.mode: True
        }

        train_op = self.model.train_op
        total_loss = self.model.total_loss
        data_loss = self.model.data_loss
        reg_term = self.model.reg_term

        mrImgs = self.model.x
        preds = self.model.pred
        ctImgs = self.model.y
        summary = self.model.summary_op

        return self.sess.run([train_op, total_loss, data_loss, reg_term, mrImgs, preds, ctImgs, summary],
                             feed_dict=feed)

    def test(self, x, batch_size):
        num_data = x.shape[0]
        preds = np.zeros_like(x)

        for i in range(0, num_data, batch_size):
            x_batch = x[i:i+batch_size]

            feed = {
                self.model.x: x_batch,
                self.model.mode: False
            }

            step_preds = self.sess.run(self.model.pred, feed_dict=feed)
            preds[i:i+batch_size] = step_preds

        return preds

    def init(self):
        self.sess.run(tf.global_variables_initializer())

    @staticmethod
    def evaluate(gts, preds, masks):
        gts_ = intransform(gts, is_squeeze=False, dtype=np.float32) * masks
        preds_ = intransform(preds, is_squeeze=False, dtype=np.float32) * masks

        mae = cal_mae(gts_, preds_)
        me = cal_me(gts_, preds_)
        mse = cal_mse(gts_, preds_)
        pcc = cal_pcc(gts_, preds_)

        return mae, me, mse, pcc

    @staticmethod
    def save_imgs(mrImgs, ctImgs, preds, masks, iter_time=None, save_folder=None):
        num_data, h, w, c = mrImgs.shape

        for i in range(num_data):
            mask = np.squeeze(masks[i])
            canvas = np.zeros((h, 3*w), dtype=np.uint8)
            canvas[:, :w] = inv_transform(mrImgs[i])          # Input MR image
            canvas[:, w:2*w] = inv_transform(preds[i]) * mask  # Predicted CT image
            canvas[:, -w:] = inv_transform(ctImgs[i])         # GT CT image

            if iter_time is None:
                imgName = os.path.join(save_folder, '{}'.format(str(i).zfill(3))) + '.png'
            else:
                imgName = os.path.join(save_folder, '{}_{}'.format(str(iter_time).zfill(6), str(i).zfill(3))) + '.png'

            cv2.imwrite(imgName, canvas)

