# Contrato inicial com o backend

A versão `0.1.0-alpha.1` conhece somente as ações abaixo:

| Ação na interface | Comando fixo | Condição |
|---|---|---|
| Apply Desktop Configuration | `sh instalar.sh` | `instalar.sh` existe no backend |
| Run Diagnostics | `make diagnostico` | `Makefile` contém o alvo |
| Refresh Nix Apps | executável instalado `refresh-nix-apps` ou `atualizar-aplicativos-nix` | arquivo executável encontrado no PATH do usuário |

O backend é localizado automaticamente em `~/alpine-desktop`, `~/Documents`,
`~/Downloads` ou `~/Music`. A variável `ALPINE_DESKTOP_BACKEND` permite indicar
outro diretório.

Esse contrato é propositalmente pequeno durante a fase alfa. Novas ações devem
ser adicionadas como operações nomeadas e documentadas, nunca como campos de
comando arbitrário.
