## Tutorial de Instalação do Portainer (e dependências)

```d
senha root: uperWym202x2 --- rompendiocKh
senha n8n: 63_U2<-1t3qJ
```

Este tutorial organiza os comandos fornecidos para instalar o Portainer, juntamente com as dependências e configurações relacionadas, como Docker Swarm, rede overlay e um exemplo de deploy do Traefik (embora não seja estritamente necessário para o Portainer, está nos comandos).

**Observações:**

*   Este tutorial assume que você está em um sistema Linux baseado em Debian/Ubuntu (devido ao uso do `apt-get`).
*   Os comandos são executados no terminal.
*   O arquivo `traefik.yaml` e `portainer.yaml` precisam ser criados com o conteúdo apropriado (não fornecido aqui).

**Passo 1: Preparação do Sistema**

1.  **Atualizar lista de pacotes e instalar utilitário AppArmor:**
    Além de atualizar a lista de pacotes, o `apparmor-utils` é instalado, o que pode ser útil para gerenciar perfis AppArmor relacionados a contêineres.

    ````d
sudo apt-get update && sudo apt-get install -y apparmor-utils
    ````


**Passo 2: Instalação do Docker**

1.  **Instalar o Docker:**
    Este comando baixa e executa um script da Docker para instalar a versão estável do Docker Engine.

````d
sudo curl -fsSL https://get.docker.com | bash
````

**Passo 3: Inicialização do Docker Swarm**

1.  **Inicializar o Docker Swarm:**
    Este comando inicia o modo Swarm no nó atual, tornando-o o nó manager inicial.

````d
  .  sudo docker swarm init
    
````

**Passo 4: Configuração da Rede Overlay**

1.  **Criar uma rede overlay:**
    Redes overlay permitem comunicação entre serviços em diferentes nós de um cluster Swarm. Esta rede `network_public` pode ser usada por seus serviços.

````d
sudo docker network create --driver=overlay network_public

````


**Passo 5: Deploy do Traefik (Opcional, mas nos comandos)**

1.  **Criar o arquivo de configuração do Traefik:**
    Você precisará criar um arquivo chamado `traefik.yaml` com a configuração desejada para o Traefik, um proxy reverso e load balancer.

````d
nano traefik.yaml
````

2.  **Deploy do Traefik como um stack Docker:**
    Este comando implanta o Traefik como um conjunto de serviços definidos no arquivo `traefik.yaml` dentro de um stack chamado `traefik`. As opções `--prune` remove serviços que não estão mais no arquivo de configuração, e `--resolve-image always` força o Docker a baixar a imagem mais recente do Traefik.

````d
sudo docker stack deploy --prune --resolve-image always -c traefik.yaml traefik
````

Erro ao baixar devido a muitas requisições ou "No such image: traefik:2.11.2"

```d
sudo docker stack ps traefik

```

**Passo 6: Instalação do Portainer**

```d
# Acesso:
username: admin
senha: uperWym202x2
```
1.  **Criar o arquivo de configuração do Portainer:**
    Você precisará criar um arquivo chamado `portainer.yaml` com a configuração para o serviço Portainer. Um exemplo básico pode incluir a imagem do Portainer, mapeamento de portas e a definição de volumes para persistência dos dados do Portainer.

````d
    nano portainer.yaml
````

Mudar a linha: 
> "traefik.http.routers.portainer.rule=Host(`portainer.server.bentektecnologia.com.br`)"

**portainer.yaml**
```d
version: "3.7"

services:
  portainer:
    image: portainer/portainer-ce:2.27.3
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    networks:
      - network_public
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints: [node.role == manager]
      labels:
        - "traefik.enable=true"
        - "traefik.docker.network=network_public"
        - "traefik.http.routers.portainer.rule=Host(`p.rennata.autom.my`)"
        - "traefik.http.routers.portainer.entrypoints=websecure"
        - "traefik.http.routers.portainer.priority=1"
        - "traefik.http.routers.portainer.tls.certresolver=letsencryptresolver"
        - "traefik.http.services.portainer.loadbalancer.server.port=9000"

networks:
  network_public:
    external: true
    attachable: true
    name: network_public

volumes:
  portainer_data:
    external: true
    name: portainer_data

```


 **Deploy do Portainer como um stack Docker:**
    Similar ao Traefik, este comando implanta o Portainer como um serviço definido no arquivo `portainer.yaml` dentro de um stack chamado `portainer`.

````d
#subir stack portainer
sudo docker stack deploy --prune --resolve-image always -c portainer.yaml portainer

````


**Passo 7: Criação das Stacks no portainer

- Subir statck do redis
- Subir stack do postgres
```d
Senha banco: uperWym202x2
```

Estes comandos demonstram a criação de bancos de dados PostgreSQL, que podem ser usados por aplicações como N8N e Chatwoot (mencionado nos nomes dos bancos de dados). **Você precisa ter o PostgreSQL instalado no seu sistema ou em um contêiner Docker separado para que esses comandos funcionem.**

1.  **Acessar o shell do PostgreSQL como o usuário `postgres`:**

````d
psql -U postgres
 ````

2.  **Criar os bancos de dados `n8ndb` e `chatwoot`:**
    Dentro do shell do `psql`, execute os seguintes comandos:

````d
    CREATE DATABASE n8ndb; CREATE DATABASE chatwoot;
````

**Passo 8. Subir stack do n8n**
- Ajustar arquivo .yaml
	- domínio
	- senha do banco
	- TimeZone
