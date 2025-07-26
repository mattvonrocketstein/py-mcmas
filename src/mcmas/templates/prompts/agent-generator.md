To populate the schema, consider the following python function source code:

{{user_query}}

To populate agent name, use the name of the top-level function.
To populate agent actions, look for other functions that are called inside the main function.
To populate agent variables, use arguments in the function header.
To populate agent obsvars, use variable names that are involved with the return value.  If return value is dictionary, use the dictionary keys.