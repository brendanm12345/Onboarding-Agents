from src.agents.browser_gym.action_library import (
    navigate_to_data_source,
    set_date_range,
    enter_ticker,
    add_variables,
    set_output_options,
    perform_query_and_download,
)

from browsergym.core.action.highlevel import HighLevelActionSet

def custom_action_mapping(action_str: str) -> str:
    """
    An extension of browser gym default action space that allows us to execute learned workflows
    TODO: this function will have to support all functions that we ever learn from demonstration, right now we've hardcoded actions from one demo
    """
    # extract the action from within triple backticks
    import re
    match = re.search(r'```(.+?)```', action_str, re.DOTALL)
    if not match:
        raise ValueError("No action found within triple backticks")
    
    action_str = match.group(1).strip()
    print(f"Extracted action: {action_str}")
    
    if action_str.startswith("STANDARD."):
        # Handle standard BrowserGym actions
        action_part = action_str[len("STANDARD."):]
        try:
            action_code = HighLevelActionSet().to_python_code(action_part)
            return action_code
        except Exception as e:
            raise ValueError(f"Error parsing STANDARD action '{action_part}': {e}")
    
    elif action_str.startswith("WORKFLOW."):
        # Handle custom workflow actions
        action_part = action_str[len("WORKFLOW."):]
        
        # Split on first occurrence of '('
        if '(' not in action_part:
            raise ValueError(f"Invalid WORKFLOW action format: '{action_str}'. Must include parentheses.")
            
        workflow_name, args_str = action_part.split('(', 1)
        args_str = args_str.rstrip(')')  # Remove closing parenthesis
        workflow_name = workflow_name.strip()
        
        try:
            if workflow_name == "add_variables":
                # Extract the list directly using regex
                variables_match = re.search(r'variables=\[(.*?)\]', args_str)
                if not variables_match:
                    raise ValueError("Could not parse variables list")
                # Split the comma-separated values and clean them
                variables = [v.strip().strip("'").strip('"') for v in variables_match.group(1).split(',')]
                return add_variables(variables=variables)
            
            # Regular argument parsing for other functions
            kwargs = {}
            if args_str.strip():
                for arg_pair in args_str.split(','):
                    if '=' in arg_pair:
                        key, value = arg_pair.strip().split('=', 1)
                        kwargs[key.strip()] = value.strip().strip("'").strip('"')
            
            # Map to appropriate workflow function
            if workflow_name == "navigate_to_data_source":
                return navigate_to_data_source()
            elif workflow_name == "set_date_range":
                if 'start_date' not in kwargs or 'end_date' not in kwargs:
                    raise ValueError("set_date_range requires start_date and end_date")
                return set_date_range(start_date=kwargs['start_date'], end_date=kwargs['end_date'])
            elif workflow_name == "enter_ticker":
                if 'ticker' not in kwargs:
                    raise ValueError("enter_ticker requires ticker")
                return enter_ticker(ticker=kwargs['ticker'])
            elif workflow_name == "set_output_options":
                if 'email' not in kwargs:
                    raise ValueError("set_output_options requires email")
                return set_output_options(email=kwargs['email'])
            elif workflow_name == "perform_query_and_download":
                return perform_query_and_download()
            else:
                raise ValueError(f"Unknown workflow action: {workflow_name}")
                
        except Exception as e:
            raise ValueError(f"Error parsing WORKFLOW action '{action_part}': {e}")
    
    else:
        raise ValueError(f"Unknown action type. Must start with 'STANDARD.' or 'WORKFLOW.'")