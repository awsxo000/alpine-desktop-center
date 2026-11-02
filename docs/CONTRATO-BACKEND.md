# Contrato do backend

A interface usa operações nomeadas e não executa texto arbitrário informado
pelo usuário. O backend `alpine-desktop` continua sendo a fonte de verdade.

## Ações globais

| Ação | Comando fixo |
|---|---|
| Apply Full Configuration | `sh instalar.sh` — saída compacta |
| Apply Full Configuration with Diagnostics | `make diagnostico` — execução detalhada |
| Refresh Nix Apps | `~/.local/bin/atualizar-aplicativos-nix.sh` |

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

O backend executa a operação ou diagnóstico; a persistência do histórico é
responsabilidade do frontend. Cada módulo possui sua própria pasta:

```text
~/.local/state/alpine-desktop-center/logs/<versao-frontend>/<modulo>/execution.log
~/.local/state/alpine-desktop-center/logs/<versao-frontend>/<modulo>/diagnostics/<data-e-hora>.json
```

Essa é a estrutura oficial e exclusiva do contrato atual; arquivos planos
antigos na raiz de `logs/` não são importados nem exibidos.

Cada release usa seu próprio namespace de logs, por exemplo
`logs/0.1.0-alpha.21/`. Assim, uma instalação nova começa sem registros da
release anterior. Cada clique em **Check Status** cria um novo arquivo JSON;
nenhuma verificação é anexada ao arquivo de outra verificação.

A interface mostra o log global na aba **Overview**. Na aba **Modules**, o
botão **Check Status** atualiza uma fotografia atual do estado do módulo, sem
substituir os arquivos históricos. O botão **View Module Log** mostra primeiro
o registro salvo mais recente, depois o log de execução e todos os arquivos de
diagnóstico anteriores em uma lista selecionável, com separadores por ponto. O
acesso à pasta fica dentro desse histórico, no botão com ícone de pasta, que
abre diretamente a pasta do módulo selecionado no gerenciador de arquivos.

## Diagnóstico de integridade

O status do módulo não é mais inferido por uma única verificação silenciosa.
Quando o backend atualizado está disponível, a interface chama:

```sh
make diagnostico-modulo MODULO=<modulo>
```

Essa operação é somente leitura e retorna JSON versionado (`schema_version: 1`)
com o estado geral, cada componente verificado, avisos, falhas e dependências.
O backend continua sendo a fonte de verdade dos critérios de integridade; o
frontend apenas apresenta o resultado e grava uma cópia em:

```text
~/.local/state/alpine-desktop-center/logs/<versao-frontend>/<modulo>/diagnostics/<data-e-hora>.json
```

O arquivo `execution.log` permanece reservado à saída de aplicações reais do
Ansible. Verificações não são adicionadas a esse log, evitando comandos
repetidos e mantendo separados diagnóstico e alteração do sistema. O status
atual exibido na interface é efêmero; o histórico persistido continua nos
arquivos `execution.log` e `diagnostics/*.json`.
