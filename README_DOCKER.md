## Инструкции для запуска образа:
1) Без дополнительных параметров
    - docker run -it --rm vladislave008/bash-simulator:latest
2)	С blind-mount для hot-reload (актуально для разработчиков)
    - docker run -it --rm -v ${PWD}:/app vladislave008/bash-simulator:latest
3)	Для проверки HEALTHCHECK
    - docker run -d -it --rm vladislave008/bash-simulator:latest
    - docker ps

## Инструкции по сборке образа:
1)	Простая сборка с двумя тегами:
    docker build --no-cache -t vladislave008/bash-simulator:latest -t vladislave008/bash-simulator:1.0.0 .
2)	Multi-arch сборка (amd64, arm64):
    docker buildx build --platform linux/amd64,linux/arm64 -t vladislave008/bash-simulator:latest -t vladislave008/bash-simulator:1.0.0 --push .
