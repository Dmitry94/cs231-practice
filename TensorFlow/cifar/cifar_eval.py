"""
    Cifar evaluation on test script.
"""

import argparse
import math
import os
import time
import h5py
from datetime import datetime
import numpy as np

import cifar_input
import tensorflow as tf


def eval_once(app_args, saver):
    """
        Run Eval once.
        Args:
        saver: Saver.
        summary_writer: Summary writer.
        top_k_op: Top K op.
        summary_op: Summary op.
    """
    config = tf.ConfigProto(device_count={"GPU": app_args.gpu_count})
    sess = tf.InteractiveSession(config=config)
    saver.restore(sess, tf.train.latest_checkpoint(app_args.checkpoint_dir))
    coord = tf.train.Coordinator()

    train_hdf5 = h5py.File(app_args.data_file, "r")
    manager = cifar_input.Cifar10DataManager(
        app_args.batch_size, train_hdf5["data"], train_hdf5["labels"],
        coord, app_args.data_format)

    images, labels = tf.get_collection("inputs")
    logits = tf.get_collection("logits")[0]
    loss = tf.get_collection(tf.GraphKeys.LOSSES)[0]
    top_k_op = tf.nn.in_top_k(logits, labels, 1)

    num_iter = int(math.ceil(app_args.samples_count / app_args.batch_size))
    true_count = 0
    total_sample_count = num_iter * app_args.batch_size
    step = 0
    loss_mean = 0

    while step < num_iter and not coord.should_stop():
        im_feed, l_feed = manager.next_batch()
        loss_val, predictions = sess.run(
            [loss, top_k_op], feed_dict={images: im_feed,
                                         labels: l_feed})
        loss_mean += loss_val
        true_count += np.sum(predictions)
        step += 1

    precision = true_count / float(total_sample_count)
    print("%s: Precision = %f, Loss = %f" % (datetime.now(), precision,
                                             (loss_mean / step)))

    coord.request_stop()
    sess.run(manager.queue.close(cancel_pending_enqueues=True))


def evaluate(app_args):
    graph_path = ""
    for file in os.listdir(app_args.checkpoint_dir):
        if file.endswith(".meta"):
            if file > graph_path:
                graph_path = file
    graph_path = os.path.join(app_args.checkpoint_dir, graph_path)
    saver = tf.train.import_meta_graph(graph_path)
    while True:
        eval_once(app_args, saver)
        if app_args.eval_once:
            break
        else:
            time.sleep(app_args.eval_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file",
                        help="Path to the data directory",
                        default="../../content/ciraf/hdf5/test.hdf5")

    parser.add_argument("--samples-count", type=int,
                        help="Number of images to process at all",
                        default=10000)

    parser.add_argument("--batch-size", type=int,
                        help="Number of images to process in a batch",
                        default=256)

    parser.add_argument("--log-dir",
                        help="Path to the directory, where log will write",
                        default="cifar10_eval")

    parser.add_argument("--checkpoint-dir",
                        help="Path to the directory, where checkpoint stores",
                        default="cifar10_train")

    parser.add_argument("--eval-interval", type=int,
                        help="How often to evaluate",
                        default=10)

    parser.add_argument("--eval-once", type=bool,
                        help="Eval one time or more",
                        default=False)

    parser.add_argument("--data-format",
                        help="Data format: NCHW or NHWC",
                        default="NHWC")

    parser.add_argument("--gpu-count", type=int,
                        help="Count of GPUs, if zero, then use CPU",
                        default=0)

    app_args = parser.parse_args()
    if tf.gfile.Exists(app_args.log_dir):
        tf.gfile.DeleteRecursively(app_args.log_dir)
    tf.gfile.MakeDirs(app_args.log_dir)
    tf.logging.set_verbosity("DEBUG")
    evaluate(app_args)
