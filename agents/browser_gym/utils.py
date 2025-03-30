import base64
import io
from PIL import Image
import numpy as np

def image_to_jpg_base64_url(image: np.ndarray | Image.Image):
    """Convert a numpy array to a base64 encoded image url."""

    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    if image.mode in ("RGBA", "LA"):
        image = image.convert("RGB")

    with io.BytesIO() as buffer:
        image.save(buffer, format="JPEG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/jpeg;base64,{image_base64}"

def deduplicate_axtree(axtree_text: str, threshold: int = 50) -> str:
    """
    Deduplicates repetitive elements in AXTree text while preserving structure.
    
    Args:
        axtree_text: String containing the AXTree text representation
        threshold: Minimum number of similar elements before collapsing
        
    Returns:
        Filtered AXTree text with collapsed duplicate sections
    """
    lines = axtree_text.split('\n')
    filtered_lines = []
    current_group = []
    current_pattern = None
    
    def get_element_pattern(line: str) -> tuple:
        """Extract the key pattern from a line, excluding the ID."""
        # Handle indentation
        indent = len(line) - len(line.lstrip())
        line = line.strip()
        
        # Skip non-element lines
        if not line.startswith('['):
            return (indent, line)
            
        # Extract the core pattern without the ID
        try:
            # Remove the ID section
            core = line[line.index(']') + 1:].strip()
            # Create pattern tuple including indent and attributes
            return (indent, core)
        except ValueError:
            return (indent, line)
    
    def format_group(group: list, count: int) -> list:
        """Format a group of similar elements."""
        if count <= threshold:
            return group
        
        # Keep the first element
        result = [group[0]]
        # Add the summary line with proper indentation
        indent = ' ' * (len(group[0]) - len(group[0].lstrip()))
        pattern = get_element_pattern(group[0])[1]
        result.append(f"{indent}[... {count-1} similar elements: {pattern} ...]")
        return result
    
    for line in lines:
        if not line.strip():
            continue
            
        pattern = get_element_pattern(line)
        
        # Handle non-element lines or different indentation levels
        if not pattern[1].startswith('checkbox') or pattern != get_element_pattern(current_group[0]) if current_group else None:
            # Process any existing group
            if current_group:
                filtered_lines.extend(format_group(current_group, len(current_group)))
                current_group = []
            filtered_lines.append(line)
            continue
        
        # Continue building current group
        current_group.append(line)
    
    # Process the last group if it exists
    if current_group:
        filtered_lines.extend(format_group(current_group, len(current_group)))
    
    return '\n'.join(filtered_lines)
