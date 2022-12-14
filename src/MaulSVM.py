from ctypes import *
import platform

class MaulSVM:

  labels = []
  values = []

  finalized = False

  def __init__(self, params):

    # Validate kernel
    if params.dataType == "vector":
      if params.kernelName not in ["linear","poly","RBF"]:
        raise ValueError("Invalid Vector Kernel!")
    else:
      if params.kernelName not in ['edit', 'subseq']:
        raise ValueError('Invalid String Kernel!')

    # Store the parameters
    self.params = params

    # Load libSVM
    if platform.system() == "Windows":
      self.svmlib = cdll.LoadLibrary("../libsvm-string/libsvm-string-win32.dll");#WIN32
    else:
      self.svmlib = cdll.LoadLibrary("../libsvm-string/libsvm.so.2");# *NIX
      # Set the prototypes on the functions we care about

    # Prototypes
    self.svmlib.svm_train.restype = POINTER(svm_model)
    self.svmlib.svm_train.argtypes = [POINTER(svm_problem), POINTER(svm_parameter)]
    self.svmlib.svm_predict_p.restype = c_double
    self.svmlib.svm_predict_p.argtypes = [POINTER(svm_model), POINTER(svm_data)]
    self.svmlib.svm_free_and_destroy_model.restype = None
    self.svmlib.svm_free_and_destroy_model.argtypes = [POINTER(POINTER(svm_model))]
    self.svmlib.svm_save_model.restype = c_int
    self.svmlib.svm_save_model.argtypes = [c_char_p, POINTER(svm_model)]
    self.svmlib.svm_load_model.restype = POINTER(svm_model)
    self.svmlib.svm_load_model.argtypes = [c_char_p]

  def __del__(self):
    try:
      self.model
    except AttributeError:
      return
    # do nothing
    else:
      self.svmlib.svm_free_and_destroy_model(pointer(self.model))
      return

  # Takes a list of (string, value) tuples, and stores them
  def addSamples(self, samples):
    newLabels, newValues = zip(*samples)
    self.labels = self.labels + list(newLabels)
    self.values = self.values + list(newValues)

  # Takes a single sample and stores it
  def addSample(self, label, value):
    self.labels.append(label)
    self.values.append(value)

  # Finalizes the training data. No more data may be added
  def finalize(self):

    # Validate
    if not self.values:
      raise RuntimeError("No training data!")

    # Generate a mapping from string labels to numbers
    self.labelMap = dict()
    self.reverseLabelMap = dict()
    for i, label in enumerate(set(self.labels)):
      self.labelMap[label] = i
      self.reverseLabelMap[i] = label

    # Generate a numerical label list
    self.labelsNumeric = map(lambda x : self.labelMap[x], self.labels)

    # Flag that we're finalized
    self.finalized = True

  def train(self):

    # Validate
    if (hasattr(self, 'model')):
      raise RuntimeError("Already have a model!")
    if (not self.finalized):
      raise RuntimeError("Must call finalize() before calling train()!")

    # Generate the problem
    problem = svm_problem(self.params, self.labelsNumeric, self.values)

    # Generate the parameters
    params = svm_parameter(self.params)

    # Generate the model
    self.model = self.svmlib.svm_train(problem, params)

  def predict(self, val):

    # Validate
    if not hasattr(self, 'model'):
      raise RuntimeError("Need to call train() first!")

    # Make a prediction
    query = svm_data()
    query.initialize(self.params, val)
    prediction = self.svmlib.svm_predict_p(self.model, pointer(query))

    return self.reverseLabelMap[int(prediction)]

  def svm_save_model(self,model_file_name):
    """
	svm_save_model(model_file_name, model) -> None
    Save a LIBSVM model to the file model_file_name.
    """
    if not hasattr(self,'model'):
        raise RuntimeError('need to train first!')
    # need to save labels so loading can get them too       
    labelfile = model_file_name+'.labels'    
    f = open(labelfile,'w')
    for i,label in enumerate(set(self.labels)):
        s = label +':'+str(i)+'\n'
        f.write(s)
    f.close()
    self.svmlib.svm_save_model(model_file_name, self.model)

  def svm_load_model(self,model_file_name):
    """
    svm_load_model(model_file_name) -> model
    Load a LIBSVM model from model_file_name and return.
    """
    model = self.svmlib.svm_load_model(model_file_name)
    if not model: 
      print("can't open model file %s" % model_file_name)
      return None
    self.model = self.toPyModel(model)
    print 'SVM MODEL LOADED'
    #self.model = model
 # load in labels   
    labelfile = model_file_name + '.labels' 
    f = open(labelfile,'r')
    self.labelMap = dict()
    self.reverseLabelMap = dict()
    for line in f:
        s = line.split(':')
        label = s[0]
        i = int(s[1].strip().rstrip())
        self.labels.append(s[0])
        self.labelMap[label] = i
        self.reverseLabelMap[i] = label
    self.labelsNumeric = map(lambda x : self.labelMap[x], self.labels)    
    print 'svm labels:'
    print self.labelMap
    return self.model 



  def toPyModel(self,model_ptr):
    """
    toPyModel(model_ptr) -> svm_model
    Convert a ctypes POINTER(svm_model) to a Python svm_model
    """
    if bool(model_ptr) == False:
        raise ValueError("Null pointer")
    m = model_ptr.contents
    m.__createfrom__ = 'C'
    return m



"""
Python Wrappers for C Data Structures

These inherit special magic from ctypes.Structure
"""
SVM_TYPE_C_SVC = 0
KERNEL_TYPE_LINEAR = 0
KERNEL_TYPE_POLY = 1
KERNEL_TYPE_RBF = 2
KERNEL_TYPE_EDIT = 5
KERNEL_TYPE_SUBSEQ = 6
DATA_TYPE_VECTOR = 0
DATA_TYPE_STRING = 1
DATA_TYPE_TOKENS = 2
class svm_parameter(Structure):
  _fields_ = [("svm_type", c_int),
              ("data_type", c_int),
              ("kernel_type", c_int),
              ("degree", c_int),
              ("gamma", c_double),
              ("coef0", c_double),
              ("cache_size", c_double),
              ("eps", c_double),
              ("C", c_double),
              ("nr_weight", c_int),
              ("weight_label", POINTER(c_int)),
              ("weight", POINTER(c_double)),
              ("nu", c_double),
              ("p", c_double),
              ("shrinking", c_int),
              ("probability", c_int)]

  def __init__(self, params):
    Structure.__init__(self)

    # Set kernel
    if params.kernelName == "edit":
      self.kernel_type = KERNEL_TYPE_EDIT
    elif params.kernelName == "subseq":
      self.kernel_type = KERNEL_TYPE_SUBSEQ
    elif params.kernelName == "linear":
      self.kernel_type = KERNEL_TYPE_LINEAR
    elif params.kernelName == "poly":
        self.kernel_type = KERNEL_TYPE_POLY
    elif params.kernelName == "RBF":
        self.kernel_type = KERNEL_TYPE_RBF
    else:
      raise ValueError("Unknown kernel!")


    # Set data_type
    if (params.dataType == "string"):
      self.data_type = DATA_TYPE_STRING
    elif (params.dataType == "tokens"):
      self.data_type = DATA_TYPE_TOKENS
    elif (params.dataType == "vector"):
      self.data_type = DATA_TYPE_VECTOR
    else:
      raise ValueError("Unknown dataType " + param.dataType + "!")

    # Set C
    self.C = params.C

    # Shrinking
    # The subsequence kernel tends to ask for -h 0 when it's run
    if params.kernelName == "subseq":
      self.shrinking = 0
    else:
      self.shrinking = 1

    # Tweakable params
    self.gamma = params.gamma
    self.degree = params.degree
    self.coef0 = params.coef0

    # Untweakable params
    self.svm_type = SVM_TYPE_C_SVC
    self.cache_size = 100
    self.eps = 1e-3
    self.nr_weight = 0
    self.weight_label = None
    self.weight = None
    self.nu = 0.5
    self.p = 0.1
    self.probability = 0

class svm_model(Structure):
  _fields_ = []

class svm_node(Structure):
  _fields_ = [("index", c_int),
              ("value", c_double)]

class svm_data(Structure):
  _fields_ = [("v", POINTER(svm_node)),
              ("s", c_char_p),
              ("t", POINTER(c_uint)),
              ("libsvm_allocated", c_int)]

  # Fills an svm_data structure with appropriate values
  def initialize(self, params, val):
    if (params.dataType == "string"):
      self.v = None
      self.t = None
      self.s = val

    elif (params.dataType == "tokens"):
      self.v = None
      self.s = None
      self.t = (c_uint * (len(val) + 1))()
      self.t[0] = len(val) # First element of a token string is the length
      for j, num in enumerate(val):
        self.t[j+1] = num

    elif (params.dataType == "vector"):
      self.t = None
      self.s = None

      # Vectors are stored in a sparse format where each node
      # is an index of the next non-zero component and its value
      self.v = (svm_node * (len(val) + 1))()
      for j, tuple in enumerate(val):
        self.v[j].index = tuple[0]
        self.v[j].value = tuple[1]

      # Set the sentinel
      self.v[len(val)].index = -1
      self.v[len(val)].value = 123456

    else:
      raise ValueError("Unknown dataType parameter!")


class svm_problem(Structure):
  _fields_ = [("l", c_int),
              ("y", POINTER(c_double)),
              ("x", POINTER(svm_data))]

  def __init__(self, params, labels, values):

    # Validate
    if (len(labels) != len(values)):
      raise ValueError("Need equal number of values and labels!")

    # Set the length
    self.l = len(labels)

    # Set the labels
    #
    # According to the ctypes tutorial, "The recommended way to create array
    # types is by multiplying a data type with a positive integer". Um, ok...
    self.y = (c_double * self.l)()
    for i, label in enumerate(labels): self.y[i] = label

    # Set the values
    self.x = (svm_data * self.l)()
    for i, val in enumerate(values):
      self.x[i].initialize(params, val)
