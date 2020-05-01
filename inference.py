import os
import sys
import getopt
import visualize
import numpy as np
import tensorflow as tf

from matplotlib import pyplot as plt

from detection.datasets import coco, data_generator
from detection.datasets.utils import get_original_image
from detection.models.detectors import faster_rcnn

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

assert tf.__version__.startswith('2.')

tf.random.set_seed(22)
np.random.seed(22)

img_mean = (123.675, 116.28, 103.53)
# img_std = (58.395, 57.12, 57.375)
img_std = (1., 1., 1.)

batch_size = 1
flip_ratio = 0
learning_rate = 1e-4

opts, args = getopt.getopt(sys.argv[1:], "-b:-f:-l:", )

train_dataset = coco.CocoDataSet(dataset_dir='dataset', subset='train',
                                 flip_ratio=flip_ratio, pad_mode='fixed',
                                 mean=img_mean, std=img_std,
                                 scale=(800, 1216))

train_generator = data_generator.DataGenerator(train_dataset)
train_tf_dataset = tf.data.Dataset.from_generator(
    train_generator, (tf.float32, tf.float32, tf.float32, tf.int32))
train_tf_dataset = train_tf_dataset.batch(batch_size).prefetch(100).shuffle(100)

num_classes = len(train_dataset.get_categories())
model = faster_rcnn.FasterRCNN(num_classes=num_classes)

# inference

img, img_meta, bboxes, labels = train_dataset[6]
rgb_img = np.round(img + img_mean)
ori_img = get_original_image(img, img_meta, img_mean)
visualize.display_instances(rgb_img, bboxes, labels, train_dataset.get_categories())

plt.savefig('img_demo.png')

batch_imgs = tf.convert_to_tensor(np.expand_dims(img, 0))  # [1, 1216, 1216, 3]
batch_metas = tf.convert_to_tensor(np.expand_dims(img_meta, 0))  # [1, 11]

model.load_weights('model/epoch_10.h5', by_name=True)

proposals = model.simple_test_rpn(img, img_meta)
res = model.simple_test_bboxes(img, img_meta, proposals)
visualize.display_instances(ori_img, res['rois'], res['class_ids'],
                            train_dataset.get_categories(), scores=res['scores'])

plt.savefig('image_demo_ckpt.png')


