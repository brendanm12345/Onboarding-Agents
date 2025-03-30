import os
import re
import types
import inspect
from typing import Dict, Callable
from playwright.sync_api import Page, expect

def create_wrapper(func, params, source_code=None):
    """
    Creates a wrapper around a workflow function that converts it into executable code string.
    
    Args:
        func: The original workflow function
        params: List of parameters (excluding 'page')
        source_code: Optional source code of the function
    """
    def wrapper(**kwargs):
        # Use stored source code if available, otherwise try to get it from func
        source = wrapper._source_code
        
        # Create the implementation string & add imports
        impl = []
        impl.append("from playwright.sync_api import expect")
        impl.append("import re")  # add in case regex is used in the function
        
        # Split into lines and process the function body
        lines = source.split('\n')
        
        # Find the first non-empty line that's not the function definition or docstring
        start_idx = 0
        base_indent = None
        in_docstring = False
        triple_quote = None
        
        for i, line in enumerate(lines):
            if i == 0:  # skip function definition
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
                
            # First real line of source code
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
        
        impl.extend(impl_lines)
        
        # Join all lines with proper newlines
        impl_str = '\n'.join(impl)
        
        # Substitute actual arguments into the code
        for arg_name, arg_value in kwargs.items():
            if isinstance(arg_value, list):
                arg_str = f"[{', '.join(repr(x) for x in arg_value)}]"
                impl_str = re.sub(rf'\b{arg_name}\b(?!\s*=)', arg_str, impl_str)
            else:
                impl_str = re.sub(rf'\b{arg_name}\b(?!\s*=)', repr(arg_value), impl_str)
        
        return impl_str.strip()

    # Store original function and signature for introspection
    wrapper.original_func = func
    wrapper.__signature__ = inspect.Signature(parameters=params)
    wrapper.__doc__ = func.__doc__  # Preserve the docstring
    wrapper._source_code = source_code  # Store the source code
    
    return wrapper

def load_workflow_functions(workflows_base_dir: str = None) -> Dict[str, Callable]:
    """
    Dynamically discovers and loads all functions from verified_workflow.py files in the workflows directory,
    excluding main_workflow functions.
    """
    workflow_functions = {}
    
    # Get the workflows directory path
    if workflows_base_dir is None:
        workflows_base_dir = 'workflows'
    
    print(f"Searching for workflows in: {workflows_base_dir}")
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(workflows_base_dir):
        print(f"\nChecking directory: {root}")
        print(f"Found files: {files}")
        
        if 'verified_workflow.py' in files:
            module_path = os.path.join(root, 'verified_workflow.py')
            print(f"\nFound workflow file: {module_path}")
            
            try:
                # Read the module source first
                with open(module_path, 'r') as f:
                    module_source = f.read()
                print(f"Successfully read module source, length: {len(module_source)}")
                
                # Remove the playwright execution at the bottom if it exists
                if "if __name__ == '__main__':" in module_source:
                    module_source = module_source.split("if __name__ == '__main__':")[0]
                    print("Removed __main__ block")
                elif "with sync_playwright() as playwright:" in module_source:
                    module_source = module_source.split("with sync_playwright() as playwright:")[0]
                    print("Removed playwright execution block")
                
                # Create a module from the modified source
                module_name = f"workflow_{os.path.basename(root)}"
                module = types.ModuleType(module_name)
                
                # Add necessary imports to the module's namespace
                module.__dict__['Page'] = Page
                module.__dict__['expect'] = expect
                module.__dict__['re'] = re
                
                # Execute the modified source in the module's namespace
                exec(module_source, module.__dict__)
                
                # Extract functions and their sources
                lines = module_source.split('\n')
                current_func = None
                current_source = []
                function_sources = {}
                
                for line in lines:
                    if line.startswith('def '):
                        # If we were collecting a previous function, save it
                        if current_func and current_func != "main_workflow":
                            function_sources[current_func] = '\n'.join(current_source)
                        
                        # Start collecting new function
                        func_match = re.match(r'def\s+(\w+)\s*\(', line)
                        if func_match:
                            current_func = func_match.group(1)
                            current_source = [line]
                    elif current_func:
                        current_source.append(line)
                        # Check if function has ended (empty line after indented block)
                        if line.strip() == '' and current_source[-2].strip() == '':
                            if current_func != "main_workflow":
                                function_sources[current_func] = '\n'.join(current_source)
                            current_func = None
                            current_source = []
                
                # Don't forget the last function
                if current_func and current_func != "main_workflow":
                    function_sources[current_func] = '\n'.join(current_source)
                
                print(f"Found functions: {list(function_sources.keys())}")
                
                # Get all functions from the module
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if name != "main_workflow" and not name.startswith("_"):
                        try:
                            if name in function_sources:
                                print(f"Processing function: {name}")
                                # Create a wrapper that removes the 'page' parameter from signature
                                sig = inspect.signature(obj)
                                params = list(sig.parameters.values())
                                
                                # Remove 'page' parameter if it exists
                                if params and params[0].name == "page":
                                    params = params[1:]
                                    
                                workflow_functions[name] = create_wrapper(
                                    obj, 
                                    params,
                                    source_code=function_sources[name]
                                )
                                print(f"Successfully created wrapper for: {name}")
                        except Exception as e:
                            print(f"Error processing function {name}: {e}")
                            continue
                
            except Exception as e:
                print(f"Error loading workflow from {module_path}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    print(f"\nTotal functions loaded: {len(workflow_functions)}")
    return workflow_functions

if __name__ == "__main__":
    print(load_workflow_functions())