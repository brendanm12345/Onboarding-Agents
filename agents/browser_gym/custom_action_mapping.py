import os
import inspect
import importlib.util
import re
from typing import Dict, Callable, Any
from browsergym.core.action.highlevel import HighLevelActionSet

def create_wrapper(func, params):
    def wrapper(**kwargs):
        # Get the function's source code
        source = inspect.getsource(func)
        
        # Start with the expect import
        impl = "from playwright.sync_api import expect\n"
        
        # Split into lines and find the start of the actual implementation
        lines = source.split('\n')
        
        # Find the first non-empty line that's not the function definition or docstring
        start_idx = 0
        base_indent = None
        in_docstring = False
        triple_quote = None
        
        for i, line in enumerate(lines):
            if i == 0:  # Skip function definition
                continue
                
            stripped = line.strip()
            if not stripped:
                continue
                
            # Handle docstring detection
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                in_docstring = True
                triple_quote = stripped[:3]
                continue
            elif in_docstring and triple_quote in stripped:
                in_docstring = False
                continue
            elif in_docstring:
                continue
                
            # First real line of implementation
            if not in_docstring:
                base_indent = len(line) - len(line.lstrip())
                start_idx = i
                break
        
        # Extract implementation lines, preserving relative indentation
        impl_lines = []
        for line in lines[start_idx:]:
            if not line.strip():  # Keep empty lines as is
                impl_lines.append('')
                continue
            
            current_indent = len(line) - len(line.lstrip())
            # Only remove the base indentation level
            if current_indent >= base_indent:
                impl_lines.append(line[base_indent:])
            else:
                impl_lines.append(line)
        
        impl += '\n'.join(impl_lines)
        
        # Substitute actual arguments into the code
        for arg_name, arg_value in kwargs.items():
            if isinstance(arg_value, list):
                arg_str = f"[{', '.join(repr(x) for x in arg_value)}]"
                impl = re.sub(rf'\b{arg_name}\b(?!\s*=)', arg_str, impl)
            else:
                impl = re.sub(rf'\b{arg_name}\b(?!\s*=)', repr(arg_value), impl)
        
        return impl.strip()

    # Store original function
    wrapper.original_func = func
    wrapper.__signature__ = inspect.Signature(parameters=params)
    return wrapper

def load_workflow_functions(workflows_base_dir: str = None) -> Dict[str, Callable]:
    """
    Dynamically discovers and loads all functions from verified_workflow.py files in the workflows directory,
    excluding main_workflow functions.
    
    Args:
        workflows_base_dir (str, optional): Base directory to search for workflows. 
            If None, uses current directory's 'workflows' folder.
    
    Returns:
        Dict[str, Callable]: Dictionary mapping function names to their implementations
    """
    workflow_functions = {}
    
    # Get the workflows directory path
    if workflows_base_dir is None:
        workflows_base_dir = 'workflows'
    
    print(f"Searching for workflows in: {workflows_base_dir}")
    
    # Walk through all subdirectories
    for root, _, files in os.walk(workflows_base_dir):
        if 'verified_workflow.py' in files:
            module_path = os.path.join(root, 'verified_workflow.py')
            
            try:
                # Load the module dynamically
                module_name = f"workflow_{os.path.basename(root)}"
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                with open(module_path, 'r') as f:
                    module_source = f.read()
                
                # Get all functions from the module
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    # Skip main_workflow and private functions
                    if name != "main_workflow" and not name.startswith("_"):
                        try:
                            source = inspect.getsource(obj)
                            # Check if the function definition appears in the module source
                            if f"def {name}(" in module_source:
                                # Create a wrapper that removes the 'page' parameter from signature
                                sig = inspect.signature(obj)
                                params = list(sig.parameters.values())
                                
                                # Remove 'page' parameter if it exists
                                if params and params[0].name == "page":
                                    params = params[1:]
                                    
                                workflow_functions[name] = create_wrapper(obj, params)
                        except (OSError, TypeError):
                            # This can happen for built-ins or imports
                            continue
                
            except Exception as e:
                print(f"Error loading workflow from {module_path}: {e}")
                continue
                
    return workflow_functions

def get_workflow_action_space_description(url: str = None) -> str:
    """
    Generates a description of the workflow action space, including function signatures,
    docstrings, and implementation details.
    """
    try:
        workflow_functions = load_workflow_functions()
        
        if not workflow_functions:
            return "# Available Workflow Actions\n\nEach action can be called using the format: ```WORKFLOW.action_name(args)```\n\nN/A"
        
        def extract_function_info(func_obj):
            try:
                original_func = func_obj.original_func
                
                sig = func_obj.__signature__
                
                params = [p for p in sig.parameters.values()]
                sig_str = f"({', '.join(str(p) for p in params)})"
                docstring = inspect.getdoc(original_func) or "No description available"
                source = inspect.getsource(original_func)
                url_match = re.search(r'expect\(page\).to_have_url\("([^"]+)"\)', source)
                url_constraint = url_match.group(1) if url_match else None
                implementation = func_obj()
                
                return {
                    'signature': sig_str,
                    'docstring': docstring,
                    'implementation': implementation,
                    'url_constraint': url_constraint
                }
            except Exception as e:
                print(f"Error in extract_function_info: {str(e)}")
                raise
    
        # Build the description
        description = "# Available Workflow Actions\n\n" if not url else f"# Available Workflow Actions for Current URL: {url}\n\n"
        description += "Each action can be called using the format: ```WORKFLOW.action_name(args)```\n\n"
        
        for func_name, func_obj in sorted(workflow_functions.items()):
            try:
                info = extract_function_info(func_obj)
                
                # Skip if URL is provided and this function has a URL constraint that doesn't match
                if url and info['url_constraint']:
                    if not (url == info['url_constraint']):
                        print(f"Skipping this workflow function {info["signature"]} due to URL constraint")
                        continue
                
                description += f"## {func_name}{info['signature']}\n\n"
                description += f"**Description:**\n{info['docstring']}\n\n"
                
                if info['url_constraint']:
                    description += f"**URL Constraint:** This action requires being on a page matching:\n{info['url_constraint']}\n\n"
                
                description += "**Implementation:**\n```python\n"
                description += info['implementation']
                description += "\n```\n\n"
                
            except Exception as e:
                description += f"Error extracting info for {func_name}: {e}\n\n"
        
        return description

    except Exception as e:
        print(f"Error in get_workflow_action_space_description: {str(e)}")
        return f"Error generating workflow description: {str(e)}"

def custom_action_mapping(action_str: str, workflows_dir: str = None) -> str:
    """
    Maps action strings to their implementations, supporting both standard BrowserGym actions
    and custom workflow actions.
    
    Args:
        action_str (str): The action string in the format ```ACTION.function_name(args)```
        workflows_dir (str, optional): Directory containing workflow files
        
    Returns:
        str: The Python code to execute the action
    """
    # Extract the action from within triple backticks
    match = re.search(r'```(.+?)```', action_str, re.DOTALL)
    if not match:
        raise ValueError("No action found within triple backticks")
    
    action_str = match.group(1).strip()
    
    if action_str.startswith("STANDARD."):
        # Handle standard BrowserGym actions
        action_part = action_str[len("STANDARD."):]
        try:
            return HighLevelActionSet().to_python_code(action_part)
        except Exception as e:
            raise ValueError(f"Error parsing STANDARD action '{action_part}': {e}")
    
    elif action_str.startswith("WORKFLOW."):
        # Load all available workflow functions
        workflow_functions = load_workflow_functions(workflows_dir)
        
        if not workflow_functions:
            raise ValueError(f"No workflow functions found in directory: {workflows_dir}")
        
        # Parse action and arguments
        action_part = action_str[len("WORKFLOW."):]
        if '(' not in action_part:
            raise ValueError(f"Invalid WORKFLOW action format: '{action_str}'. Must include parentheses.")
        
        workflow_name, args_str = action_part.split('(', 1)
        args_str = args_str.rstrip(')')
        workflow_name = workflow_name.strip()
        
        if workflow_name not in workflow_functions:
            raise ValueError(f"Unknown workflow action: {workflow_name}")
            
        # Parse arguments
        kwargs = {}
        if args_str.strip():  # Only parse args if there's content between the parentheses
            if workflow_name == "add_variables":
                # Special handling for list arguments
                variables_match = re.search(r'variables=\[(.*?)\]', args_str)
                if variables_match:
                    variables = [v.strip().strip("'").strip('"') for v in variables_match.group(1).split(',')]
                    kwargs['variables'] = variables
            else:
                # Regular argument parsing for non-empty args
                for arg_pair in args_str.split(','):
                    arg_pair = arg_pair.strip()
                    if arg_pair and '=' in arg_pair:
                        key, value = arg_pair.split('=', 1)
                        kwargs[key.strip()] = value.strip().strip("'").strip('"')
        
        # Execute the workflow function
        return workflow_functions[workflow_name](**kwargs)
    
    else:
        raise ValueError(f"Unknown action type. Must start with 'STANDARD.' or 'WORKFLOW.'")

"""TESTS"""

def test_workflow_description():
    """Test the workflow action space description function"""
    print("\nTesting workflow action space description...")
    
    # Test without URL constraint
    print("\n1. Testing without URL:")
    description = get_workflow_action_space_description()
    print(description)
    
    # Test with specific URL
    # test_url = "https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/fundamentals-annual/"
    # print("\n2. Testing with specific URL:")
    # description = get_workflow_action_space_description(url=test_url)
    # print(description)

def test_all_workflow_mappings():
    """Tests all discovered workflow functions with sample inputs"""
    print("\nTesting all workflow mappings...")
    
    # Sample test inputs for different function types
    test_inputs = {
        'navigate_to_data_source': '```WORKFLOW.navigate_to_data_source()```',
        'set_date_range': '```WORKFLOW.set_date_range(start_date="2019-01", end_date="2023-12")```',
        'add_variables': '```WORKFLOW.add_variables(variables=["revt", "dltt"])```',
        'enter_ticker': '```WORKFLOW.enter_ticker(ticker="MSFT")```',
        'perform_query_and_download': '```WORKFLOW.perform_query_and_download()```',
        'select_compustat_data': '```WORKFLOW.select_compustat_data()```',
        'select_fundamentals_annual': '```WORKFLOW.select_fundamentals_annual()```'
    }
    
    # Load all workflow functions
    workflow_functions = load_workflow_functions()
    
    print(f"\nFound {len(workflow_functions)} workflow functions")
    print("Testing each function mapping:\n")
    
    for func_name in workflow_functions:
        print(f"\n{'='*80}")
        print(f"Testing function: {func_name}")
        print('='*80)
        
        if func_name in test_inputs:
            try:
                result = custom_action_mapping(test_inputs[func_name])
                print(f"\nInput action: {test_inputs[func_name]}")
                print(f"\nGenerated code:\n{result}")
                
                # Basic validation
                assert result.strip(), "Empty result"
                assert 'expect' in result, "Missing expect import"
                assert not result.startswith('def'), "Contains function definition"
                assert not any(line.startswith('    ') for line in result.split('\n')[0:1]), "First line is indented"
                
                print("\n✓ Validation passed")
                
            except Exception as e:
                print(f"\n✗ Error testing {func_name}: {e}")
        else:
            print(f"No test input defined for {func_name}")

if __name__ == "__main__":
    test_workflow_description()
    # test_all_workflow_mappings()