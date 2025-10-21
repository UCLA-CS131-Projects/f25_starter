import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np
from element import Element
from intbase import InterpreterBase


def plot_ast(ast_root, figsize=None):
    """
    Plot an AST structure showing each node as a box with its type and fields.

    Args:
        ast_root: Root Element of the AST
        figsize: Tuple of (width, height) for the figure. If None, will be calculated dynamically.
    """
    # Track node positions and connections
    node_positions = {}
    connections = []

    def calculate_node_width(node):
        """Calculate the width needed for a node based on its fields and array contents"""
        num_fields = len(node.dict)
        if num_fields == 0:
            return 1.8

        # Start with base width calculation
        base_width = max(1.8, num_fields * 1.2)

        # Find the largest array and add generous padding
        max_array_width = 0
        for field_name, field_value in node.dict.items():
            if isinstance(field_value, list) and len(field_value) > 0:
                # Calculate full array width including the actual box sizes
                # Each box is 0.35 wide, spaced 0.4 apart, so:
                # Total width = (n-1) * 0.4 + 0.35 = n * 0.4 - 0.05
                array_width = (
                    len(field_value) * 0.4 + 0.35 - 0.4
                )  # More precise calculation
                max_array_width = max(max_array_width, array_width)

        # If we have large arrays, ensure we have enough space
        # Use a generous approach: ensure each field can accommodate its largest array
        # plus add extra padding for safety
        if max_array_width > 0:
            # Calculate required width more generously
            # Each field needs at least enough space for its content
            # Plus we need extra space for field spacing and margins
            required_width = base_width
            extra_width_needed = max_array_width - (base_width / num_fields - 0.3)
            if extra_width_needed > 0:
                required_width = (
                    base_width + extra_width_needed + 1.0
                )  # Add 1.0 for safety margin
            return max(1.8, required_width)

        return base_width

    def layout_tree(node, x, y, level=0, min_spacing=1.2):
        """Recursively layout the tree and collect node positions with compact spacing"""
        if node is None:
            return 0, 0

        # Calculate width needed for this node
        node_width = calculate_node_width(node)

        # Calculate width needed for this subtree
        total_width = 0
        child_positions = []
        child_widths = []

        # Process all fields
        for field_name, field_value in node.dict.items():
            if isinstance(field_value, Element):
                # Single child node
                child_width, _ = layout_tree(
                    field_value, x + total_width, y - 1.2, level + 1, min_spacing
                )
                child_positions.append(
                    (field_name, field_value, x + total_width, y - 1.2)
                )
                child_widths.append(child_width)
                total_width += max(child_width, min_spacing)
            elif isinstance(field_value, list):
                # Array of child nodes
                array_width = 0
                for i, child in enumerate(field_value):  # Show all items
                    if isinstance(child, Element):
                        child_width, _ = layout_tree(
                            child, x + total_width, y - 1.2, level + 1, min_spacing
                        )
                        child_positions.append(
                            (f"{field_name}[{i}]", child, x + total_width, y - 1.2)
                        )
                        child_widths.append(child_width)
                        total_width += max(child_width, min_spacing)
                        array_width += max(child_width, min_spacing)
            else:
                # Primitive value (string, int, bool)
                total_width += 1.0

        # Ensure minimum width for the node itself
        total_width = max(total_width, node_width + 0.5)

        # Store node position
        node_positions[node] = (x + total_width / 2, y)

        # Store connections
        for field_name, child_node, child_x, child_y in child_positions:
            connections.append((node, child_node, field_name))

        return total_width, 1

    # Layout the tree with compact spacing
    tree_width, _ = layout_tree(ast_root, 0, 9, min_spacing=1.2)

    # Calculate dynamic figure size based on tree width
    if figsize is None:
        # Add padding and ensure minimum size
        required_width = max(15, tree_width + 2)  # Add 2 units of padding
        figsize = (required_width, 10)

    fig, ax = plt.subplots(figsize=figsize)

    # Set x-axis limits based on tree width
    ax.set_xlim(-1, tree_width + 1)  # Add 1 unit padding on each side
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Draw nodes
    for node, (x, y) in node_positions.items():
        # Calculate box dimensions based on number of fields and array contents
        num_fields = len(node.dict)
        box_height = 0.8  # Fixed height for type + fields + values
        box_width = calculate_node_width(node)  # Use the dynamic width calculation

        # Draw main node box
        node_box = FancyBboxPatch(
            (x - box_width / 2, y - box_height / 2),
            box_width,
            box_height,
            boxstyle="round,pad=0.02",
            facecolor="lightblue",
            edgecolor="black",
            linewidth=1,
        )
        ax.add_patch(node_box)

        # Add node type at top
        ax.text(
            x,
            y + box_height / 2 - 0.1,
            node.elem_type,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

        # Calculate field spacing with compact layout
        if num_fields > 0:
            field_spacing = (box_width - 0.3) / num_fields  # Reduced padding
            field_start_x = x - box_width / 2 + 0.15
        else:
            field_spacing = 0
            field_start_x = x

        # Draw fields and values
        for i, (field_name, field_value) in enumerate(node.dict.items()):
            field_x = field_start_x + i * field_spacing + field_spacing / 2

            # Draw field name with compact spacing
            ax.text(
                field_x,
                y + 0.15,
                field_name,
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
            )

            # Draw value box under field name
            if isinstance(field_value, Element):
                # Child node - draw pointer box
                value_box = FancyBboxPatch(
                    (field_x - 0.25, y - 0.3),
                    0.5,
                    0.3,
                    boxstyle="round,pad=0.01",
                    facecolor="lightyellow",
                    edgecolor="black",
                    linewidth=0.5,
                )
                ax.add_patch(value_box)
                ax.text(
                    field_x,
                    y - 0.15,
                    "→",
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold",
                )

                # Draw connection to child node
                if field_value in node_positions:
                    child_x, child_y = node_positions[field_value]
                    connection = ConnectionPatch(
                        (field_x, y - 0.3),
                        (child_x, child_y + 0.4),
                        "data",
                        "data",
                        arrowstyle="->",
                        shrinkA=3,
                        shrinkB=5,
                        mutation_scale=15,
                        fc="black",
                    )
                    ax.add_patch(connection)

            elif isinstance(field_value, list):
                # Array of nodes - draw array boxes
                array_width = len(field_value) * 0.4
                array_start_x = field_x - array_width / 2

                for j, child in enumerate(field_value):
                    if isinstance(child, Element):
                        array_box = FancyBboxPatch(
                            (array_start_x + j * 0.4, y - 0.3),
                            0.35,
                            0.3,
                            boxstyle="round,pad=0.01",
                            facecolor="lightyellow",
                            edgecolor="black",
                            linewidth=0.5,
                        )
                        ax.add_patch(array_box)
                        ax.text(
                            array_start_x + j * 0.4 + 0.175,
                            y - 0.15,
                            "→",
                            ha="center",
                            va="center",
                            fontsize=10,
                            fontweight="bold",
                        )

                        # Draw connection to child
                        if child in node_positions:
                            child_x, child_y = node_positions[child]
                            connection = ConnectionPatch(
                                (array_start_x + j * 0.4 + 0.175, y - 0.3),
                                (child_x, child_y + 0.4),
                                "data",
                                "data",
                                arrowstyle="->",
                                shrinkA=3,
                                shrinkB=5,
                                mutation_scale=15,
                                fc="black",
                            )
                            ax.add_patch(connection)
                    else:
                        # Primitive in array
                        array_box = FancyBboxPatch(
                            (array_start_x + j * 0.4, y - 0.3),
                            0.35,
                            0.3,
                            boxstyle="round,pad=0.01",
                            facecolor="lightyellow",
                            edgecolor="black",
                            linewidth=0.5,
                        )
                        ax.add_patch(array_box)

                        # Add value text (truncate if too long)
                        value_str = str(child)
                        if len(value_str) > 6:
                            value_str = value_str[:3] + "..."
                        ax.text(
                            array_start_x + j * 0.4 + 0.175,
                            y - 0.15,
                            value_str,
                            ha="center",
                            va="center",
                            fontsize=6,
                        )

            else:
                # Primitive value - draw value box
                value_box = FancyBboxPatch(
                    (field_x - 0.25, y - 0.3),
                    0.5,
                    0.3,
                    boxstyle="round,pad=0.01",
                    facecolor="lightyellow",
                    edgecolor="black",
                    linewidth=0.5,
                )
                ax.add_patch(value_box)

                # Add value text (truncate if too long)
                value_str = str(field_value)
                if len(value_str) > 8:
                    value_str = value_str[:5] + "..."
                ax.text(
                    field_x, y - 0.15, value_str, ha="center", va="center", fontsize=8
                )

    plt.title("AST Visualization", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.show()


# Add a call to interpreterv4's Interpreter.run method
def run_with_plotting(program_text):
    """
    Run the interpreter and plot the AST.

    Args:
        program_text: The program text to parse and run
    """
    from interpreterv1 import Interpreter
    from brewparse import parse_program

    # Parse the program to get AST
    ast = parse_program(program_text)

    # Plot the AST
    plot_ast(ast)

    # Run the interpreter
    interpreter = Interpreter()
    interpreter.run(program_text)

    return interpreter.get_output()


# Example usage
if __name__ == "__main__":
    # Example program
    example_program = """
    def main() {
        var i;
        i = 5;
        var s;
        s = "hello";
        print(i);
        print(s);
    }
    """

    output = run_with_plotting(example_program)
    print("Program output:", output)
