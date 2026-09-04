from orquestrador.orquestrador import carregar_config, criar_tarefa, executar_pipeline

def main():
    config = carregar_config()

    tarefa = criar_tarefa(config)

    resultado = executar_pipeline(tarefa)

    print(
        f"\nPipeline concluído."
        f"\nEmpresas encontradas: {resultado['quantidade_encontrada']}"
        f"\nEmpresas processadas: {resultado['quantidade_processada']}"
    )

if __name__ == "__main__":
    main()