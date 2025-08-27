
Consider the following tree:

{{ast}}

The goal is to obtain a new tree from the existing one.  Use the following heuristics:

1. Alter only the "leaf nodes" which are raw strings or lists.
2. For strings, substitute "and" for "or", and vice versa.
3. Substitute ">=" for "=<" and "true" to "false", and vice versa.
4. Add or remove parentheses to change grouping, but always ensure parentheses match
5. Change the order of expressions in lists, but not move them outside of the list they appear in.
6. Swap the names of variables: {{variables}}

Requirements for response:
1. Do not explain yourself, and output only valid JSON.
2. Do not include text before or after the JSON response.

JSON Response:
