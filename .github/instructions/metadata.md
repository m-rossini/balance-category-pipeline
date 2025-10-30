# Metadata Feature Description
This feature will collect metadata and runtime collection of a pipeline and its steps.
Each step will have some of its runtime and parameters capture, the same being true for the whole pipeline
## Objectives
The objectives of this features are many fold as follows, always refering to both the pipeline and each steps unless noted otherwise:
 * Understand how long a given pipeline and its steps took to run
 * Understand the parameters of a spacific run
 * Understand the history of run
 * Learn about the volumes for input and output of each step and the pipeline itself.
 * I want to understand the quality of the final results. For that we will discuss later, for now a place holder for quality index suffice
 * The data is going to be permanent and I want uniquely identify a given run
 * The location of the data about the run, i.e. the metadata, should be configurable, but defaulted when omitted, therefore the help file and readme should also be updated
 * Pipeline runner should create and save the metadata data
 * Remember that datapipeline IS ONLY configuration as code