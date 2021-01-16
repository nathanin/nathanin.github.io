---
title: "Self supervision in bioimage analysis"
tags: [machine-learning]
---

## Self supervision in bioimage analysis

An often cited double-edged sword in bioimaging is the over-abundance of unlabelled data.
On one hand, platforms like MIBI [REF], CyTOF [REF], CODEX [REF], and plain old H&E staining produce images with 
100,000 cells or more.
But the volume of data and specialized knowledge required to interpret it means that almost none of it is annotated.
Thus, techniques from self/semi/un-supervised family represent a powerful framework for working with bioimaging datasets.

<!-- What do I mean by annotated?
Annotations come at multiple scales: 

  - sample-level annotations (age, gender, disease status, etc.)
  - microscopic annotations annotations (growth pattern, cell type)
  - subcellular architecture, mitotic figures, apoptosis, cellular function

These come with unique advantages:

  - easy to acquire, define and interpret
  - rich image representation, related to common pathology practice
  - close to underlying biology, flexibility

and disadvantages:

  - complicates learning
  - murky definitions (see: Gleason Grading)
  - even murkier definitions, highly sensitive features often required
 -->

So what do we do?

<!-- Let's consider two case studies and how two lines of analysis from the same source data can look very different based on the questions we ask, and which combinations of the above annotation we have to work with.  -->

Our way forward varies depending on the actual goal, but the first move is broadly the same as always:
We want to take our highly dimensional data and summarize each data point in a low-dimension representation. 
In the original data, different variables (e.g. genes, genomic positions, XY coordinates in an image) will have complex semantic relationships or covariance with other variables.
These features should capture an aspect of the high-dimensional covariation, and together recapitulate all the pertinent information in the original data. 
(Bonus if each feature captures a __unique__ (or disentangled) aspect of the high-dimensional data.)

The golden example of such a technique is principle components analysis (PCA), and related techniques like singular value decomposition (SVD).
... We need a technique that will deal with unordered, shuffled, and noisy data. 

### Contrastive learning

Self-supervision takes many forms, centered around the idea that data flow through a bottleneck should allow some function on the other side of the bottleneck to recover information resembling the original data.
Autoencoders and variational autoencoders frame this problem by actually asking the original data to be recoverable through the bottleneck.
Contrastive learning tries to encode two views of the same data point to a similar space on the low-dimensional manifold. 


### Case study 1: growth pattern classification

I'm of the opinion that segmentation, detection, and classification tasks framed to recapitulate known well-defined annotations are rarely interesting in a vacuum. 
These things absolutely have to come with a question to provide a context.
Nevertheless, these classic problems remain unsolved in general, and solutions continue to yield intersting technical advances.


### Case study 2: niche detection

One of the many promises of next-generation imaging is the discovery of new ways that cells organize and communicate in-situ.
Since they're new, well, that means no one knows exactly what to look for yet. 


version draft 0

January 15, 2021