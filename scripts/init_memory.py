from backend.app.services.memory_manager import memory_manager
from backend.app.services.vault_manager import vault_manager


def main() -> None:
    memory_manager.ensure_vault_structure()
    vault_manager.ensure_vault_structure()
    print(f"Initialized Cortex brain vault at: {memory_manager.get_memory_path()}")
    print(f"Initialized user vault at: {vault_manager.get_vault_path()}")


if __name__ == "__main__":
    main()
