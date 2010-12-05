from MaulProblem import MaulProblem
import sqlite3
import random

class MaulDataset:

  # Constructor
  def __init__(self, dbName, params):

    # Store Params
    self.params = params
    self.dbName = dbName

  # Standard Cross-Validation Routine
  def crossValidate(self, category, trainingProportion, totalProportion, constraints):

    # Load the samples
    self.loadSamples(category, constraints)

    # Select the training data
    self.prepareTrainingData(trainingProportion, totalProportion)

    # Make a decision problem
    problem = MaulProblem(category, self.params)

    # If the model is not already generated, generate it
    if not problem.haveModel():
      problem.generateModel(trainingData)
      problem.saveModel()
    else:
      problem.loadModel()

  # Helper routine to load the samples into a dictionary
  def loadSamples(self, category, constraints):

    # Open Database
    conn = sqlite3.connect(self.dbName)
    conn.text_factory = str
    c = conn.cursor()

    # Query
    c.execute('select uaString, Tokens, ' + category + ' from data ' + constraints)

    # Organize our samples by label (tracking the maximum token while we do it)
    self.maxToken = 0
    self.samples = dict()
    for item in c:
      label = item[2]
      uaString = item[0]
      tokens = [int(s) for s in item[1].split(' ')]
      self.maxToken = max(self.maxToken, max(tokens))
      if not self.samples.has_key(label):
        self.samples[label] = []
      self.samples[label].append({"uaString" : uaString, "tokens": tokens, "label" : label})


  # Helper routine to pull some samples out into an array of training data
  def prepareTrainingData(self, trainingProportion, totalProportion):

    # Process the data to extract training data (everything that remains
    # is test data)
    self.trainingData = []
    print "Processing Samples..."
    for key in self.samples.keys():

      # Shuffle the data
      random.shuffle(self.samples[key])

      # If we want to use less than our total amount of data (for speed),
      # shrink the list now
      if totalProportion < 1.0:
        del self.samples[key][int(len(self.samples[key]) * totalProportion):]

      # Pick out training data
      numTrainingSamples = int(len(self.samples[key]) * trainingProportion)
      for i in range(1, numTrainingSamples):
        self.trainingData.append(self.prepareSample(self.samples[key].pop()))
      print "Selected " + str(numTrainingSamples) + " samples of type " + key + " for "\
            "training, leaving " + str(len(self.samples[key])) + " for validation"


  # Helper routine to put a sample in the format MaulSVM expects given
  # the problem parameters
  def prepareSample(self, sample):

    if self.params.dataType == "string":
      return (sample["label"], sample["uaString"])
    elif self.params.dataType == "tokens":
      return (sample["label"], sample["tokens"])
    elif self.params.dataType == "vector":
      vec = [0] * self.maxToken
      for i in sample["tokens"]:
        vec[i] += 1
      return (sample["label"], vec)
    else:
      raise ValueError("Unknown datatype: " + str(self.params.dataType))
