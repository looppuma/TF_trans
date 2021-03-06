#==============================================================================
# 1. 下载并加载minist数据集，分为训练集和测试集
# 2. 使用线性分类器模型进行特征向量的分类，训练结果进行评估打分(传统模型效果基线)
#3. 使用卷积网络模型进行分类，训练结果进行评估打分(新模型效果比对)
#   3.1. 通过图像宽/高/色彩通道得到4维特征张量
#   3.2. 使用卷积第一层为5x5的块计算32个特征--->池化降维
#   3.3. 使用卷积第一层为5x5的块计算64个特征--->池化降维--->张量整形为一组向量
#   3.4. 1024个神经元的全连接层
#   3.5. 计算logits估计值和损失值
#   3.6. 训练操作
#   3.7. 计算评估预测准确度   
#==============================================================================

"""This showcases how simple it is to build image classification networks.

It follows description from this TensorFlow tutorial:
    https://www.tensorflow.org/versions/master/tutorials/mnist/pros/index.html#deep-mnist-for-experts
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf

N_DIGITS = 10    # Number of digits.模型对象个数0-9
X_FEATURE = 'x'  # Name of the input feature.输入特征的名称

#卷积模型函数
#输入：特征，标签，模式
def conv_model(features, labels, mode): 
  """2-layer convolution model. 2层卷积模型"""
  # Reshape feature to 4d tensor with 2nd and 3rd dimensions being
  # image width and height final dimension being the number of color channels.
  # 用第二维（图片宽度）和第三维（图片高度），第四维(颜色通道的数目)来重塑特征为四维张量
  # 特征=tf重塑函数（特征【输入名称】，【-1, 28, 28, 1])，要将数据输入进二维的卷积网络，
  # 首先要进行一次reshape，把[batch, 784]的数据变成[-1, 28, 28, 1]，其中
  # batch位填入“-1”可以自适应输入，width和height为输入图像的原始宽高，最后一位是原始图像的通道数1（灰度图为单通道）；
  feature = tf.reshape(features[X_FEATURE], [-1, 28, 28, 1])

  # First conv layer will compute 32 features for each 5x5 patch
  # 1.卷积层将会对每个5x5的块计算32个特征
  #声明第一层卷积，输入28*28*1，输出28*28*32，get_variable()函数的控制器，其定义一个作用域空间，在该空间下，
  # 通过get_variable()获得的变量的variable_name都加一个命名空间的前缀，即namespace/variable_name；
  with tf.variable_scope('conv_layer1'):
    h_conv1 = tf.layers.conv2d(
        feature,
        filters=32, #卷积核数量
        kernel_size=[5, 5], #卷积核大小
        padding='same',  #积的边界处理方式，有valid和same两种方式，valid方式不会在原有输入的基础上
        # 添加新的像素，same表示需要对input的边界数据进行填存
        activation=tf.nn.relu) #要采用的激活函数。
    h_pool1 = tf.layers.max_pooling2d(
        h_conv1, pool_size=2, strides=2, padding='same')
    #构建2维池化（要被池化的输入Tensor，池化窗口的大小，进行池化操作的步长， ）
  # Second conv layer will compute 64 features for each 5x5 patch.
  # 2.卷积层将会对每个5x5的块计算64个特征
  with tf.variable_scope('conv_layer2'):
    h_conv2 = tf.layers.conv2d(
        h_pool1,
        filters=64,
        kernel_size=[5, 5],
        padding='same',
        activation=tf.nn.relu)
    h_pool2 = tf.layers.max_pooling2d(
        h_conv2, pool_size=2, strides=2, padding='same')
    # reshape tensor into a batch of vectors
    h_pool2_flat = tf.reshape(h_pool2, [-1, 7 * 7 * 64])

  # Densely connected layer with 1024 neurons.用1024个神经元来全链接层
  #该链接层有1024个神经元，输入Tenso维度：[-1, 7 * 7 * 64]，输出为【batchsize，1024】
  h_fc1 = tf.layers.dense(h_pool2_flat, 1024, activation=tf.nn.relu)
  #对全连接层的数据加入dropout操作，防止过拟合，50%的数据会被dropout
  h_fc1 = tf.layers.dropout(
      h_fc1, 
      rate=0.5, 
      training=(mode == tf.estimator.ModeKeys.TRAIN))

  # Compute logits (1 per class) and compute loss.计算logits层（每类1个）并计算损失
  #Logits层，对dropout层的输出Tensor，执行分类操作
  输入Tensor维度：[batch_size, 1024]，输出维度[batch_size, N_DIGITS]
  logits = tf.layers.dense(h_fc1, N_DIGITS, activation=None)

  # Compute predictions.预测，
  predicted_classes = tf.argmax(logits, 1)  #预测的结果中最大值即种类
  if mode == tf.estimator.ModeKeys.PREDICT:
    predictions = {
        'class': predicted_classes,  #拼成列表[[3],[2]]格式
        'prob': tf.nn.softmax(logits) #把[-1.3,2.6,-0.9]规则化到0~1范围,表示可能性
    }
    return tf.estimator.EstimatorSpec(mode, predictions=predictions)
   #返回的是一个EstimatorSpec对象（模式，预测值=预测值）
  # Compute loss.计算损失
  loss = tf.losses.sparse_softmax_cross_entropy(labels=labels, logits=logits)
  #计算logits和labels之间的稀疏softmax交叉熵，
  # Create training op. 创建训练计划
  if mode == tf.estimator.ModeKeys.TRAIN: #假如，模型等于训练中预测模式
    optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01)
    #优化值等于用梯度下降的优化值（学习速率等于0.01）

    train_op = optimizer.minimize(loss, global_step=tf.train.get_global_step())
    #训练操作=优化值中的最小值（损失值，全局训练步骤=全局训练步骤函数）
    return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)
    # 返回的是一个EstimatorSpec对象（模式，训练操作=训练操作）
  # Compute evaluation metrics.计算评估指标
  eval_metric_ops = {       #迭代评估操作={‘正确率’：度量正确率函数（标记=标记，预测=预测类）
      'accuracy': tf.metrics.accuracy(
          labels=labels, predictions=predicted_classes)
  }
  return tf.estimator.EstimatorSpec(
      mode, loss=loss, eval_metric_ops=eval_metric_ops)
  # 返回的是一个EstimatorSpec对象（模式，损失，迭代度量操作=度量操作）

#main函数
def main(unused_args):
  tf.logging.set_verbosity(tf.logging.INFO) #可通过tensorboard来看出训练过程中
  # loss accuracy的变化。打开cmd 进入python, tensorboard --logdir=c:/***(日志保存的路径)
  
  ### Download and load MNIST dataset.
  ### 下载/加载数据集
  mnist = tf.contrib.learn.datasets.DATASETS['mnist']('/tmp/mnist')  #对mnist进行赋值为
  #数据集【mnist】（’路径‘）
  train_input_fn = tf.estimator.inputs.numpy_input_fn(   #训练输入函数fn=numpy输入函数
      x={X_FEATURE: mnist.train.images},                 #x={x特征：mnist训练图像），
      y=mnist.train.labels.astype(np.int32),             #y=标志的类型（32位）
      batch_size=100,                                    #批尺寸为100
      num_epochs=None,                                   #数据代数为空
      shuffle=True)
  test_input_fn = tf.estimator.inputs.numpy_input_fn(
      x={X_FEATURE: mnist.train.images},
      y=mnist.train.labels.astype(np.int32),
      num_epochs=1,
      shuffle=False)

  ### Linear classifier.
  ### 线性分类器
  feature_columns = [                     #特征栏
      tf.feature_column.numeric_column(
          X_FEATURE, shape=mnist.train.images.shape[1:])]
      #特征数据栏（x特征，形状=训练图片中的形状的第一行仍一列）
  classifier = tf.estimator.LinearClassifier(               #分类器为评估中的线性分类器
      feature_columns=feature_columns, n_classes=N_DIGITS)  #（特征列=特征列，n类=N_DIGIT
  classifier.train(input_fn=train_input_fn, steps=200)      #分类器的训练（输入函数fn=
  # 训练输入fn，步骤为200
  scores = classifier.evaluate(input_fn=test_input_fn)      #分数=分类器的评估函数（输入
  # 函数fn=测试输入fn）
  print('Accuracy (LinearClassifier): {0:f}'.format(scores['accuracy']))
  #打印（‘准确率（线性分类器）：{浮点数精度为1.字符串（分数【准确率】）
  ### Convolutional network
  ### 卷积网络
  classifier = tf.estimator.Estimator(model_fn=conv_model)   #线性分类器=评估函数（模型fn
  #=卷积模型）
  classifier.train(input_fn=train_input_fn, steps=200)       #分类器训练函数（输入fn=
  # 训练输入fn，步骤数为200）
  scores = classifier.evaluate(input_fn=test_input_fn)       #分数=分类器评估（输入fn=测试输入fn）
  print('Accuracy (conv_model): {0:f}'.format(scores['accuracy']))
  #打印（’准确率（卷积模型）：{位浮点}。字符串（‘准确率’）

if __name__ == '__main__': 
  tf.app.run()
