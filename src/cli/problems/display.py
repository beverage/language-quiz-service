from src.schemas.problems import Problem


# Display functions
def display_problem(problem: Problem, detailed: bool = False):
    """Display a complete problem in formatted output using Rich."""
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console()

    # Show problem details panel in detailed mode
    if detailed:
        # Create main content
        content = []

        # Title and metadata
        title = Text(f"🎯 {problem.title or 'Untitled Problem'}", style="bold cyan")
        content.append(title)
        content.append("")

        # Instructions
        instructions = Text(f"📋 {problem.instructions}", style="white")
        content.append(instructions)
        content.append("")

        # Tags
        tags_text = ", ".join(problem.topic_tags) if problem.topic_tags else "None"
        tags = Text(f"🏷️  Tags: {tags_text}", style="dim")
        content.append(tags)

        # Grammatical focus
        if hasattr(problem, "metadata") and problem.metadata:
            focus = problem.metadata.get("grammatical_focus", [])
            if focus:
                focus_text = Text(f"🎯 Focus: {', '.join(focus)}", style="yellow")
                content.append(focus_text)

        content.append("")

        # Create the main panel
        panel_content = "\n".join(str(item) for item in content)

        # Display problem details panel
        console.print()
        console.print(
            Panel(
                panel_content,
                title="Problem Details",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Always show statements table (with improved column widths)
    statements_table = Table(
        # title="📝 Statements",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    statements_table.add_column("#", style="dim", width=2)  # Reduced from 3 to 2
    statements_table.add_column("Status", width=12)  # Increased from 8 to 12
    statements_table.add_column("Content", style="white")
    statements_table.add_column("Notes", style="dim")

    for i, statement in enumerate(problem.statements):
        is_correct = statement.get("is_correct", False)

        # Status column with emoji and color
        if is_correct:
            status = Text("✓ Correct", style="bold green")
        else:
            status = Text("✗ Wrong", style="bold red")

        # Notes column (translation or explanation)
        notes = ""
        if is_correct and "translation" in statement:
            notes = f"→ {statement['translation']}"
        elif not is_correct and "explanation" in statement:
            notes = f"→ {statement['explanation']}"

        statements_table.add_row(
            str(i + 1), status, statement.get("content", ""), notes
        )

    console.print(statements_table)

    # Show footer info in detailed mode
    if detailed:
        footer_text = f"🆔 ID: {problem.id}\n📅 Created: {problem.created_at.strftime('%Y-%m-%d %H:%M')}"
        console.print(Panel(footer_text, border_style="dim", padding=(0, 2)))


def display_problem_summary(summary):
    """Display a problem summary from a ProblemSummary object using Rich."""
    from rich.console import Console
    from rich.text import Text

    console = Console()

    # Create styled summary line
    summary_text = Text()
    summary_text.append("🎯 ", style="cyan")
    summary_text.append(summary.title or "Untitled", style="bold white")
    summary_text.append(
        f" ({summary.problem_type.value}, {summary.statement_count} statements) ",
        style="dim",
    )
    summary_text.append(f"- {summary.id}", style="blue")

    console.print(summary_text)
