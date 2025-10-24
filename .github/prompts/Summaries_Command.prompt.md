---
mode: agent
---
This prmpt specfies the behavior of a new command that needs to be implemented in the pipeline.
# Summary of the Command
Implement a Summary Commnand that generates a series of difrent configurable summaries of the input data. The command should be able to produce:
- A Total Input and Output amount across ALL Data,
- A Total Input and Output amount per Year.
- A Total Input and Output amount per Month.
- An average of output by day of the month.
- An average of output of all fifths part of the month, e.g., 1-5, 6-10, 11-15, 16-20, 21-25, 26-31.
- An average of output by day of the week.
- The top 10 Largest Amounts by TransactionDescription
# Requirements
- The command should be configurable to enable or disable each of the summary types listed above.
- The command should output the summaries in a clear and structured format, such as a dictionary or a DataFrame.
- Ensure that the command handles edge cases, such as empty datasets or datasets with missing values.
- Return values must be consistent with other commands that already exist
- The command should be implemented in a way that allows for easy extension in the future, should additional summary types be required.
# Example Configuration
```json
{
  "command": "SummaryCommand",
  "args": {
    "summaries": {
      "total_input_output": true,
      "total_input_output_per_year": true,
      "total_input_output_per_month": true,
      "average_output_by_day_of_month": true,
      "average_output_by_fifths_of_month": true,
      "average_output_by_day_of_week": true,            
      "top_10_largest_by_description": true
    }
    }
