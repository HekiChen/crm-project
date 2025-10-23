"""
CRUD Generator CLI Tool.

Automatically scaffolds complete CRUD APIs for CRM entities including:
- Database models with SQLAlchemy
- Service layer with business logic
- FastAPI routers with endpoints
- Pydantic schemas for validation
- Comprehensive test suites
- Database migrations

Usage:
    crud-generate user --fields "name:str,email:str,age:int"
    crud-generate employee --domain employee --fields "first_name:str,last_name:str"
    crud-generate task --soft-delete false --audit false --dry-run
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from cli.field_parser import parse_field_definitions
from cli.file_generator import FileGenerator

app = typer.Typer(
    name="crud-generate",
    help="Generate complete CRUD scaffolding for CRM entities",
    add_completion=False,
)

console = Console()


def check_dependencies() -> bool:
    """
    Check if all required dependencies are available.

    Returns:
        bool: True if all dependencies are met, False otherwise.
    """
    missing_deps = []

    # Check for Alembic
    try:
        import alembic
    except ImportError:
        missing_deps.append("alembic")

    # Check for Jinja2
    try:
        import jinja2
    except ImportError:
        missing_deps.append("jinja2")

    # Check for SQLAlchemy
    try:
        import sqlalchemy
    except ImportError:
        missing_deps.append("sqlalchemy")

    # Check for FastAPI
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")

    if missing_deps:
        console.print("[red]Error: Missing required dependencies:[/red]")
        for dep in missing_deps:
            console.print(f"  - {dep}")
        console.print("\n[yellow]Install missing dependencies:[/yellow]")
        console.print(f"  pip install {' '.join(missing_deps)}")
        return False

    return True


@app.command()
def generate(
    entity_name: str = typer.Argument(
        ...,
        help="Name of the entity to generate (e.g., 'user', 'employee', 'customer')",
        show_default=False,
    ),
    fields: Optional[str] = typer.Option(
        None,
        "--fields",
        "-f",
        help='Field definitions in format "name:type,name:type:constraints". '
        'Example: "name:str,email:str:unique,age:int"',
    ),
    soft_delete: bool = typer.Option(
        True,
        "--soft-delete/--no-soft-delete",
        help="Enable soft delete (is_deleted, deleted_at fields)",
    ),
    timestamps: bool = typer.Option(
        True,
        "--timestamps/--no-timestamps",
        help="Add timestamp fields (created_at, updated_at)",
    ),
    audit: bool = typer.Option(
        True,
        "--audit/--no-audit",
        help="Add audit fields (created_by_id, updated_by_id)",
    ),
    domain: Optional[str] = typer.Option(
        None,
        "--domain",
        "-d",
        help="CRM domain type: 'employee', 'customer', or 'generic'",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory (default: auto-detect from project structure)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview files that would be generated without creating them",
    ),
):
    """
    Generate complete CRUD scaffolding for a CRM entity.

    Creates:
    - SQLAlchemy model (backend/app/models/<entity>.py)
    - Service layer (backend/app/services/<entity>_service.py)
    - FastAPI router (backend/app/api/<entity>s.py)
    - Pydantic schemas (backend/app/schemas/<entity>_schemas.py)
    - API tests (backend/tests/test_<entity>s_api.py)
    - Service tests (backend/tests/test_<entity>s_service.py)
    - Database migration (backend/alembic/versions/<timestamp>_create_<entity>_table.py)

    Examples:
        # Basic entity with custom fields
        crud-generate user --fields "name:str,email:str:unique,age:int"

        # Employee entity with CRM domain patterns
        crud-generate employee --domain employee --fields "first_name:str,last_name:str,hire_date:date"

        # Minimal entity without audit trails
        crud-generate task --audit false --fields "title:str,status:str"

        # Preview generation without creating files
        crud-generate product --fields "name:str,price:decimal" --dry-run
    """

    # Check dependencies first
    if not check_dependencies():
        raise typer.Exit(code=1)

    # Validate entity name
    if not entity_name:
        console.print("[red]Error: Entity name is required[/red]")
        raise typer.Exit(code=1)

    # Check for valid Python identifier
    if not entity_name.isidentifier():
        console.print(
            f"[red]Error: Invalid entity name '{entity_name}'. Must be a valid Python identifier.[/red]"
        )
        console.print(
            "[yellow]Tip: Use lowercase names without spaces or special characters (e.g., 'user', 'employee', 'work_log')[/yellow]"
        )
        raise typer.Exit(code=1)

    # Check for reserved Python keywords
    import keyword

    if keyword.iskeyword(entity_name):
        console.print(
            f"[red]Error: '{entity_name}' is a reserved Python keyword and cannot be used as an entity name.[/red]"
        )
        raise typer.Exit(code=1)

    # Check for common reserved names
    reserved_names = {
        "model",
        "schema",
        "service",
        "api",
        "test",
        "base",
        "main",
        "app",
    }
    if entity_name.lower() in reserved_names:
        console.print(
            f"[red]Error: '{entity_name}' is a reserved name and cannot be used as an entity name.[/red]"
        )
        console.print(
            f"[yellow]Tip: Try adding a prefix or suffix (e.g., '{entity_name}_entity', 'crm_{entity_name}')[/yellow]"
        )
        raise typer.Exit(code=1)

    # Parse and validate fields
    try:
        parsed_fields = parse_field_definitions(fields)
    except ValueError as e:
        console.print(f"[red]Error parsing fields: {e}[/red]")
        console.print(
            "[yellow]Tip: Use format 'name:type' or 'name:type:constraints'[/yellow]"
        )
        console.print(
            "[yellow]Example: --fields 'name:str,email:str:unique,age:int'[/yellow]"
        )
        raise typer.Exit(code=1)

    # Display banner
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]CRUD Generator[/bold cyan]\n"
            f"Generating scaffolding for entity: [yellow]{entity_name}[/yellow]",
            border_style="cyan",
        )
    )
    console.print()

    # Display configuration
    config_table = Table(title="Configuration", show_header=False, box=None)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="yellow")

    config_table.add_row("Entity Name", entity_name)
    config_table.add_row("Fields", fields or "(using defaults)")
    if parsed_fields:
        config_table.add_row("Parsed Fields", f"{len(parsed_fields)} field(s)")
    config_table.add_row("Soft Delete", "✓" if soft_delete else "✗")
    config_table.add_row("Timestamps", "✓" if timestamps else "✗")
    config_table.add_row("Audit Trail", "✓" if audit else "✗")
    config_table.add_row("Domain", domain or "generic")
    config_table.add_row("Dry Run", "✓" if dry_run else "✗")

    console.print(config_table)
    console.print()

    if dry_run:
        console.print("[yellow]Dry run mode: No files will be created[/yellow]")
        console.print()

        # Show parsed fields if any
        if parsed_fields:
            fields_table = Table(title="Parsed Fields", show_header=True)
            fields_table.add_column("Field Name", style="cyan")
            fields_table.add_column("Type", style="yellow")
            fields_table.add_column("SQLAlchemy Type", style="green")
            fields_table.add_column("Constraints", style="magenta")

            for field in parsed_fields:
                constraints_str = ", ".join(
                    [c.name for c in field.constraints] or ["none"]
                )
                fields_table.add_row(
                    field.name, field.type, field.sqlalchemy_type, constraints_str
                )

            console.print(fields_table)
            console.print()

        # Show what would be generated
        files_table = Table(title="Files to Generate", show_header=True)
        files_table.add_column("File Type", style="cyan")
        files_table.add_column("Path", style="green")

        files_table.add_row("Model", f"app/models/{entity_name}.py")
        files_table.add_row("Service", f"app/services/{entity_name}_service.py")
        files_table.add_row("API Router", f"app/api/{entity_name}s.py")
        files_table.add_row("Schemas", f"app/schemas/{entity_name}_schemas.py")
        files_table.add_row("API Tests", f"tests/test_{entity_name}s_api.py")
        files_table.add_row("Service Tests", f"tests/test_{entity_name}s_service.py")
        files_table.add_row(
            "Migration", f"alembic/versions/*_create_{entity_name}_table.py"
        )

        console.print(files_table)
        console.print()

        console.print(
            "[green]✓[/green] Dry run complete. Use without --dry-run to generate files."
        )
        return

    # Determine output directory
    if output_dir is None:
        # Auto-detect backend directory
        current_dir = Path.cwd()
        if (current_dir / "app").exists():
            output_dir = current_dir
        elif (current_dir / "backend" / "app").exists():
            output_dir = current_dir / "backend"
        else:
            console.print(
                "[red]Error: Could not auto-detect backend directory. Please specify --output-dir[/red]"
            )
            raise typer.Exit(code=1)

    # Validate output directory structure
    if not (output_dir / "app").exists():
        console.print(
            f"[red]Error: Invalid output directory '{output_dir}'. Missing 'app' subdirectory.[/red]"
        )
        raise typer.Exit(code=1)

    # Initialize file generator
    try:
        generator = FileGenerator(
            template_dir=Path(__file__).parent.parent / "templates" / "crud",
            output_dir=output_dir,
        )
    except Exception as e:
        console.print(f"[red]Error initializing generator: {e}[/red]")
        raise typer.Exit(code=1)

    # Generate all files with progress indicators
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            # Step 1: Initialize generator
            task1 = progress.add_task("[cyan]Initializing generator...", total=1)
            generator = FileGenerator(
                template_dir=Path(__file__).parent.parent / "templates" / "crud",
                output_dir=output_dir,
            )
            progress.update(
                task1, advance=1, description="[green]✓ Generator initialized"
            )

            # Step 2: Parse fields and prepare context
            task2 = progress.add_task("[cyan]Preparing templates...", total=1)
            progress.update(task2, advance=1, description="[green]✓ Templates prepared")

            # Step 3: Generate files
            task3 = progress.add_task("[cyan]Generating files...", total=7)

            generated_files, migration_path = generator.generate_all(
                entity_name=entity_name,
                fields=parsed_fields,
                soft_delete=soft_delete,
                timestamps=timestamps,
                audit=audit,
                domain=domain,
                register_router=True,
                generate_migration=True,
            )

            progress.update(
                task3, advance=7, description="[green]✓ All files generated"
            )

            # Step 4: Register router
            task4 = progress.add_task("[cyan]Registering router...", total=1)
            progress.update(task4, advance=1, description="[green]✓ Router registered")

            # Step 5: Generate migration
            if migration_path:
                task5 = progress.add_task("[cyan]Creating migration...", total=1)
                progress.update(
                    task5, advance=1, description="[green]✓ Migration created"
                )

        console.print()

        # Display generated files with icons
        success_table = Table(
            title="✓ Generated Files", show_header=True, border_style="green"
        )
        success_table.add_column("Icon", style="yellow", width=4)
        success_table.add_column("Type", style="cyan", width=15)
        success_table.add_column("Path", style="green")

        file_icons = {
            "Model": "📦",
            "Service": "⚙️",
            "API Router": "🌐",
            "Schemas": "📋",
            "API Tests": "✅",
            "Service Tests": "🧪",
            "Migration": "🔄",
        }

        for file_path in generated_files:
            # Determine file type from path
            file_name = file_path.name
            if file_name.startswith("test_") and "api" in file_name:
                file_type = "API Tests"
            elif file_name.startswith("test_"):
                file_type = "Service Tests"
            elif "service" in file_name:
                file_type = "Service"
            elif file_name.endswith("_schemas.py"):
                file_type = "Schemas"
            elif "api" in str(file_path.parent):
                file_type = "API Router"
            elif "models" in str(file_path.parent):
                file_type = "Model"
            else:
                file_type = "File"

            # Show relative path from output_dir
            try:
                rel_path = file_path.relative_to(output_dir)
            except ValueError:
                rel_path = file_path

            icon = file_icons.get(file_type, "📄")
            success_table.add_row(icon, file_type, str(rel_path))

        if migration_path:
            try:
                rel_migration = migration_path.relative_to(output_dir)
            except ValueError:
                rel_migration = migration_path
            success_table.add_row("🔄", "Migration", str(rel_migration))

        console.print(success_table)
        console.print()

        # Show router registration status
        console.print(
            "[green]✓[/green] Router automatically registered in [cyan]app/main.py[/cyan]"
        )
        console.print()

        # Success summary with statistics
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_column(style="cyan")
        stats_table.add_column(style="yellow")

        stats_table.add_row("📊 Files Generated:", str(len(generated_files)))
        stats_table.add_row("🔄 Migrations:", "1" if migration_path else "0")
        stats_table.add_row("📦 Entity:", entity_name)
        stats_table.add_row(
            "🏷️  Fields:", str(len(parsed_fields)) if parsed_fields else "default"
        )

        console.print(stats_table)
        console.print()

        # Success message
        console.print(
            Panel.fit(
                f"[bold green]✓ Successfully generated CRUD scaffolding for '{entity_name}'[/bold green]",
                border_style="green",
            )
        )
        console.print()

        # Next steps guidance
        entity_plural = entity_name + "s"
        next_steps = f"""[bold cyan]Next Steps:[/bold cyan]

[yellow]1.[/yellow] [bold]Apply the database migration:[/bold]
   [dim]$[/dim] alembic upgrade head

[yellow]2.[/yellow] [bold]Start the development server:[/bold]
   [dim]$[/dim] uvicorn app.main:app --reload

[yellow]3.[/yellow] [bold]Test the API endpoints:[/bold]
   [dim]$[/dim] curl http://localhost:8000/api/v1/{entity_plural}

[yellow]4.[/yellow] [bold]View the interactive API documentation:[/bold]
   [cyan]→[/cyan] http://localhost:8000/docs

[yellow]5.[/yellow] [bold]Run the test suite:[/bold]
   [dim]$[/dim] pytest tests/test_{entity_plural}_api.py -v
"""

        console.print(
            Panel(
                next_steps,
                title="[bold]🚀 Getting Started[/bold]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    except FileExistsError as e:
        console.print()
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        console.print(
            "[yellow]💡 Tip: Existing files are automatically backed up with .bak extension[/yellow]"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print()
        console.print(f"[bold red]✗ Error during generation:[/bold red] {e}")
        import traceback

        if console.is_terminal:
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Display the CRUD generator version."""
    console.print("[cyan]CRUD Generator[/cyan] version [yellow]1.0.0[/yellow]")


@app.callback()
def main():
    """
    CRUD Generator - Scaffold complete CRUD APIs for CRM entities.

    Automatically generates:
    - Database models with SQLAlchemy 2.0
    - Service layers with async support
    - FastAPI routers with OpenAPI docs
    - Pydantic schemas for validation
    - Comprehensive test suites
    - Alembic database migrations
    """
    pass


if __name__ == "__main__":
    app()
