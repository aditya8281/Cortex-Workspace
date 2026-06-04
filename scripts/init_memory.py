from backend.app.services.memory_manager import memory_manager


def main() -> None:
    memory_manager.ensure_vault_structure()
    print(f"Initialized Cortex brain vault at: {memory_manager.get_memory_path()}")


if __name__ == "__main__":
    main()
