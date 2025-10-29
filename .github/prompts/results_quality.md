# Results Quality
This feature objective is to measure the quality of categorization made in previous steps

## Inputs
The data categorized. It will receive the whole data frame and will use the columns Category, Subcategory and confidence to calculate a quality index.

## Outputs
The outputs will be in the form of CommandResult class wehre the data frame is the same from the input
It will create the score into the metadata parameter.

## Calculation
The calculation will be an average of each row confidence value. Confidence value per row is a range from zero (No confidence) to 1 (Full confidence).

For each row, if any of category, subcategory or confidence is missing the value for that row is zero.
If confidence is zero, regardless of anything else the confidence is zero.

Numbers below 0.70 have more weight in bringing the index down, anything between 0.71 and 0.9 is second weight and over 0.9 has a lesser weight. This is to highlight the need for a higher confidence overall. If there is any other strategy to it, let me know and ask for clairifications.

## Implementations
The calculator should be pluggable and defined in configuration. I can decide to change how to calculate it at any time.

## Interactions
The metadata will be updated with the quality index via metadata paramter in the command result.
The metadata will be updated with the name of the calculater via metadata parameter.
The Datapipeline class should read metadata info after each step, update the final metadata with the ones from the command result
