#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include "subsequence.h"

/*
 * Original code from:
 * http://www.learning-kernel-classifiers.org/code/string_kernels/strings.c
 * */

template<typename T>
void
SubseqKernel<T>::Init(unsigned maxLen, unsigned seqLength, double lambda)
{
  // Store initialization parameters
  mMaxLen = maxLen;
  mSeqLength = seqLength;
  mLambda = lambda;

  // Allocate memory for the dynamic programming cache variable
  mCache  = (double ***) malloc (mSeqLength * sizeof (double **));
  for (unsigned i = 1; i < mSeqLength; i++) {
    mCache  [i] = (double **) malloc (mMaxLen * sizeof (double *));
    for (unsigned j = 0; j < maxLen; j++)
      mCache  [i] [j] = (double *) malloc (mMaxLen * sizeof (double));
  }

  // Precompute powers of lambda
  mLambdaPows = (double *) malloc ((maxLen + 2) * sizeof(double));
  mLambdaPows[0] = 1;
  mLambdaPows[1] = mLambda;
  for (unsigned i = 2; i < maxLen + 2; ++i)
    mLambdaPows[i] = mLambdaPows[i-1] * mLambda;


  // Mark us as initialized
  mInitialized = true;
}

template<typename T>
SubseqKernel<T>::~SubseqKernel()
{
  // If we were never initialized, there's nothing to do.
  if (!mInitialized)
    return;

  // Free the DP LUT
  for (unsigned i = 1; i < mSeqLength; i++) {
    for (unsigned j = 0; j < mMaxLen; j++) 
      free(mCache[i][j]);
    free(mCache[i]);
  }
  free(mCache);

  // Free the lambda cache
  free(mLambdaPows);

  mInitialized = false;
}

template<typename T>
double
SubseqKernel<T>::Evaluate(const T *u, unsigned uLen, const T *v, unsigned vLen)
{
  // We must be initialized
  if (!mInitialized) {
    fprintf(stderr, "Trying to evaluate using subsequence kernel, but not intialized!\n");
    exit(-1);
  }

  // We're screwed if the string is too big.
  if (uLen > mMaxLen || vLen > mMaxLen) {
    fprintf(stderr, "String passed to subsequence kernel is too large! Aborting!\n");
    exit(-1);
  }

  // New strings, so blow away the parts of the cache that we're going to use
  for (unsigned i = 1; i < mSeqLength; ++i)
    for (unsigned j = 0; j < uLen; ++j)
      for (unsigned k = 0; k < vLen; ++k)
        mCache[i][j][k] = -1.0;

  // Invoke recursion
  return K(u, uLen, v, vLen, mSeqLength);
}

/*
 * Protected helper methods
 */

template<typename T>
double
SubseqKernel<T>::Kprime(const T *u, int p, const T *v, int q, int n)
{
  int j;
  double tmp;

  /* case 1: if a full substring length is processed, return*/
  if (n == 0) return (1.0);

  /* check, if the value was already computed in a previous computation */
  if (mCache [n] [p] [q] != -1.0) return (mCache [n] [p] [q]); 
  
  /* case 2: at least one substring is to short */
  if (p < n || q < n) return (0.0);
    
  /* case 3: recursion */
  for (j= 0, tmp = 0; j < q; j++) {
    if (v [j] == u [p - 1]) 
      tmp += Kprime (u, p - 1, v, j, n - 1) * mLambdaPows[q-j+1];
  }

  mCache [n] [p] [q] = mLambda * Kprime (u, p - 1, v, q, n) + tmp;
  return (mCache [n] [p] [q]);
}

template<typename T>
double
SubseqKernel<T>::K(const T *u, int p, const T *v, int q, int n)
{
  int j;
  double KP;

  /* the simple case: (at least) one string is to short */
  if (p < n || q < n) return (0.0);

  /* the recursion: use Kprime for the t'th substrings*/
  for (j = 0, KP = 0.0; j < q; j++) {
    if (v [j] == u [p - 1]) 
      KP += Kprime (u, p - 1, v, j, n - 1) * mLambda * mLambda;
  }
  
  return (K (u, p - 1, v, q, n) + KP);
}

