"""Initialize the Cortex memory vault structure.

`vault_manager` is no longer part of the codebase. Keep this script minimal
and safe: ensure the system memory directories exist and print the path.
"""

from backend.app.services.memory_manager import memory_manager


def main() -> None:
    memory_manager.ensure_vault_structure()
    print(f"Initialized Cortex brain vault at: {memory_manager.get_memory_path()}")


if __name__ == "__main__":
    main()
