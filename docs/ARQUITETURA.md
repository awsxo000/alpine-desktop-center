# Arquitetura

O projeto é dividido em dois repositórios com responsabilidades diferentes.

## Backend estável

O repositório [`alpine-desktop`](https://github.com/awsxo000/alpine) contém as
roles Ansible, os playbooks e os scripts que configuram o Alpine Linux. Ele é
a fonte de verdade e continua funcionando independentemente da interface
gráfica.

## Frontend experimental

O `alpine-desktop-center` contém somente a interface Qt, a descoberta do
backend, o lançamento de ações fixas e a apresentação dos logs. Ele não copia
roles, não edita playbooks e não interpreta comandos livres.

```text
KDE application menu
        |
        v
Alpine Desktop Center (PySide6)
        |
        +-- sh instalar.sh
        +-- make diagnostico
        +-- Refresh Nix Apps
        |
        v
alpine-desktop (Ansible backend)
```

## Segurança operacional

A alfa usa uma lista fechada de ações. O usuário não fornece uma string de
shell para execução. Cada botão é associado a um comando conhecido e executado
com o diretório de trabalho do backend detectado.

A aplicação não substitui o terminal. Caso a execução falhe, o log exibido na
janela ajuda a reproduzir a operação manualmente no backend.

## Integração KDE

O arquivo `.desktop` é instalado em `~/.local/share/applications/`. O launcher
fica em `~/.local/bin/`, permitindo abrir a aplicação pelo menu do KDE com dois
cliques e mantendo o backend separado.

Além desse modo instalado, cada Release inclui `Alpine Desktop Center.desktop`
na raiz do diretório. Esse atalho usa a localização do próprio arquivo para
abrir o launcher ao lado dele, permitindo executar a aplicação diretamente da
pasta extraída sem instalação global.
