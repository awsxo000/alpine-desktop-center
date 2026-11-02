# Contrato do backend

A interface usa operações nomeadas e não executa texto arbitrário informado
pelo usuário. O backend `alpine-desktop` continua sendo a fonte de verdade.

## Ações globais

| Ação | Comando fixo |
|---|---|
| Apply Full Configuration | `sh instalar.sh` |
| Run Full Diagnostics | `make diagnostico` |
| Refresh Nix Apps | executável conhecido instalado no perfil do usuário |

## Módulos

A aba **Modules** representa as roles do playbook principal. Cada módulo possui
tag, descrição, verificação de presença, aplicação isolada e log persistente.
A aplicação usa `ansible-playbook playbooks/site.yml --tags <tag>` e ativa a
feature flag correspondente quando a role possui uma condição global.

Os módulos disponíveis são `base`, `nix`, `steam`, `nix_opengl`, `rede`,
`bluetooth`, `audio`, `swap`, `energia`, `fontes` e `kde`.

O status é uma indicação operacional baseada em verificações fixas do sistema,
como serviço OpenRC, executável instalado, processo ativo, presença de fontes ou
swap. Ele não substitui uma execução Ansible em modo check; serve para orientar
o usuário antes de aplicar uma role.

## Logs

Cada execução de módulo é registrada em:

```text
~/.local/state/alpine-desktop-center/logs/<modulo>.log
```

A interface mostra o log global na aba **Overview** e permite abrir o log
individual pela ação **View Module Log**.
