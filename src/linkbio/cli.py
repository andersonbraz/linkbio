import click
import logging
import yaml
import http.server
import socketserver
import os
import requests
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

LOGS_DIR = Path.cwd() / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'linkbio_cli.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkBioCLI')

GITHUB_BASE_URL = "https://raw.githubusercontent.com/andersonbraz/linkbio/main"

ASSET_FILES = [
    "bg-desktop-light.jpg",
    "bg-desktop.jpg",
    "bg-mobile-light.jpg",
    "bg-mobile.jpg",
    "moon-stars.svg",
    "sun.svg",
    "favicon.svg"
]

TEMPLATE_FILES = [
    "index.html.jinja2",
    "script.js.jinja2",
    "style.css.jinja2"
]

def _run_command(command: list, cwd: Path, error_message: str):
    """Executa um comando de shell e levanta um erro em caso de falha."""
    logger.info(f"Executando comando: {' '.join(command)} em {cwd}")
    try:
        # Executa o comando, capturando a saída e garantindo que o retorno seja 0
        result = subprocess.run(command, cwd=cwd, check=True, 
                                capture_output=True, text=True)
        logger.info(f"Comando executado com sucesso. Saída: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{error_message}: {e.stderr}")
        click.echo(f"❌ Erro de Deploy: {error_message}")
        click.echo(f"Detalhes do erro: {e.stderr}")
        raise
    except FileNotFoundError:
        click.echo("❌ Erro: O comando 'git' não foi encontrado. Certifique-se de que o Git está instalado e no seu PATH.")
        raise
    return result

class LinkBioGenerator:
    """
    Gera arquivos de uma página "link in bio" usando config YAML e templates Jinja2.
    """
    
    OUTPUT_DIR_NAME = "page"
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir 
        self.assets_dir = self.root_dir / "assets"
        self.templates_dir = self.root_dir / "templates"
        self.output_dir = self.root_dir / self.OUTPUT_DIR_NAME
        
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        
        logger.info(f"Gerador inicializado. Diretório raiz: {self.root_dir}")

    def _download_file(self, url: str, destination_path: Path) -> None:
        """Faz o download de um arquivo de uma URL e salva no destino."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Download concluído: {destination_path.name}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao baixar {url}: {e}")
            raise
        except IOError as e:
            logger.error(f"Erro ao escrever arquivo {destination_path}: {e}")
            raise

    def _write_file(self, file_path: Path, content: str) -> None:
        """Escreve conteúdo de texto em um arquivo, com logging."""
        try:
            file_path.write_text(content, encoding='utf-8') 
            logger.info(f"Arquivo criado com sucesso: {file_path}")
        except IOError as e:
            logger.error(f"Erro ao criar arquivo {file_path}: {e}")
            raise
            
    def _load_config(self) -> Dict[str, Any]:
        """Carrega e valida o arquivo linkbio.yaml."""
        yaml_path = self.root_dir / "linkbio.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Arquivo 'linkbio.yaml' não encontrado em {self.root_dir}. Execute 'linkbio start' primeiro.")
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("Configuração YAML carregada com sucesso.")
            if not isinstance(config, dict):
                 raise ValueError("O conteúdo do linkbio.yaml não é um dicionário válido.")
            return config
        except yaml.YAMLError as e:
            logger.error(f"Erro ao parsear YAML: {e}")
            raise
        except ValueError as e:
            logger.error(f"Erro de validação: {e}")
            raise

    def start(self) -> None:
        """
        Cria o linkbio.yaml e baixa arquivos para assets/ e templates/.
        """
        logger.info("Iniciando start do LinkBio (criação de estrutura e download)...")
        
        self.assets_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        click.echo(f"📁 Diretórios 'assets' e 'templates' criados.")

        yaml_content = """username: 'andersonbraz_coder'
title: 'LinkBio - Anderson Braz'
avatar: 'https://avatars.githubusercontent.com/u/1479033?s=400&u=8b677aed22d26ab5b6d5fe84d9ae73a9c02143e8&v=4'
url: 'https://andersonbraz.github.io/bio/'
description: 'Project git-pages with LinkBio.'
name_author: 'Anderson Braz'
url_author: 'https://andersonbraz.com'
fav_icon: 'https://raw.githubusercontent.com/andersonbraz/linkbio/main/assets/favicon.svg'

nav:
  - text: 'Awesome Data Journey'
    url: 'https://andersonbraz.github.io'
  - text: 'Blog'
    url: 'https://andersonbraz.com'
  - text: 'Credenciais'
    url: 'https://www.credly.com/users/andersonbraz/badges'
  - text: 'Currículo'
    url: 'https://www.self.so/andersonbraz'

social:
  - icon: 'logo-github'
    url: 'https://github.com/andersonbraz'
  - icon: 'logo-instagram'
    url: 'https://instagram.com/andersonbraz_coder'
  - icon: 'logo-youtube'
    url: 'https://youtube.com/@andersonbraz_coder'
  - icon: 'logo-twitch'
    url: 'https://www.twitch.tv/andersonbraz_coder'
  - icon: 'logo-linkedin'
    url: 'https://linkedin.com/in/anderson-braz'
"""
        yaml_path = self.root_dir / "linkbio.yaml"
        self._write_file(yaml_path, yaml_content)

        click.echo("⬇️ Baixando Assets...")
        for filename in ASSET_FILES:
            url = f"{GITHUB_BASE_URL}/assets/{filename}"
            destination = self.assets_dir / filename
            self._download_file(url, destination)

        click.echo("⬇️ Baixando Templates...")
        for filename in TEMPLATE_FILES:
            url = f"{GITHUB_BASE_URL}/templates/{filename}"
            destination = self.templates_dir / filename
            # Templates são arquivos de texto, mas _download_file lida bem com ambos
            self._download_file(url, destination) 

        logger.info("Start concluído.")
        click.echo(f"\n✅ Start concluído! Estrutura inicial criada em: {self.root_dir}")
        click.echo("💡 Edite 'linkbio.yaml' e os templates/ e execute 'linkbio build'.")

    def _copy_assets_to_output(self):
        """
        CORRIGIDO: Copia o diretório assets/ (fonte) para page/assets/ (destino).
        """
        source_dir = self.assets_dir
        # O destino é um subdiretório 'assets' dentro do diretório 'page'
        destination_dir = self.output_dir / "assets" 
        
        if not source_dir.is_dir():
            logger.warning(f"Diretório assets não encontrado em {source_dir}. Pulando cópia.")
            return

        try:

            self.output_dir.mkdir(exist_ok=True) 

            if destination_dir.exists():
                shutil.rmtree(destination_dir)
                logger.info(f"Diretório antigo {destination_dir} removido.")
            
            shutil.copytree(source_dir, destination_dir)
            logger.info(f"Diretório assets copiado para {destination_dir}")
            
        except Exception as e:
            logger.error(f"Erro ao copiar diretório assets: {e}")
            click.echo(f"⚠️ Aviso: Falha ao copiar assets/ para page/assets. Erro: {e}")


    def build(self) -> None:
        """
        Cria a pasta 'page/', carrega config YAML, gera HTML/CSS/JS e COPIA OS ASSETS CORRETAMENTE.
        """
        logger.info("Iniciando build do LinkBio...")

        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"Diretório 'page' criado/verificado.")

        try:
            config = self._load_config()
        except (FileNotFoundError, yaml.YAMLError, ValueError):
            click.echo("❌ Falha no build: Verifique os logs e o arquivo linkbio.yaml.")
            return

        try:
            html_template = self.env.get_template("index.html.jinja2")
            css_template = self.env.get_template("style.css.jinja2")
            js_template = self.env.get_template("script.js.jinja2")

            self._write_file(self.output_dir / "index.html", html_template.render(**config))
            self._write_file(self.output_dir / "style.css", css_template.render())
            self._write_file(self.output_dir / "script.js", js_template.render())
            
            self._copy_assets_to_output() 
            
            logger.info("Build concluído.")
            click.echo(f"✅ Build concluído! Arquivos gerados em: {self.output_dir}")
            click.echo("💡 Use 'linkbio preview' para visualizar a página.")

        except Exception as e:
            logger.error(f"Erro durante a renderização ou escrita: {e}")
            click.echo(f"❌ Erro durante o build: {e}")

    def _get_github_remote_url(self) -> str:
        """Obtém a URL do repositório remoto (origin) do projeto raiz."""
        logger.info("Tentando obter a URL do repositório remoto.")
        try:
            # Comando: git config --get remote.origin.url
            result = _run_command(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=self.root_dir,
                error_message="Não foi possível obter a URL do repositório remoto. Verifique se a pasta é um repositório Git e se 'origin' está configurado."
            )
            url = result.stdout.strip()
            # Garante que a URL é a forma HTTPS/SSH para evitar problemas de autenticação
            if url.startswith('git@'):
                # Ex: git@github.com:user/repo.git -> https://github.com/user/repo.git
                url = url.replace('git@github.com:', 'https://github.com/').replace('.git', '') + '.git'
            elif url.startswith('https://'):
                pass
            else:
                 raise ValueError("URL remota não reconhecida.")
            
            logger.info(f"URL remota obtida: {url}")
            return url

        except Exception as e:
            # Não conseguindo obter a URL, pede-se que o usuário a insira
            click.echo(f"⚠️ Aviso: Falha ao detectar URL remota. {e}")
            url = input("Por favor, insira a URL SSH/HTTPS completa do seu repositório GitHub: ").strip()
            return url


    def publish(self) -> None:
        """
        Gera o conteúdo e faz o deploy do diretório 'page/' para a branch 'gh-pages'.
        """
        click.echo("🛠️ Executando build antes do deploy...")
        self.build() # Garante que o conteúdo de 'page/' está atualizado

        if not self.output_dir.is_dir():
            click.echo(f"❌ Erro: Diretório de deploy esperado ({self.output_dir}) não encontrado após o build.")
            return

        # 1. Obter a URL do repositório
        repo_url = self._get_github_remote_url()
        if not repo_url:
            click.echo("❌ Deploy cancelado: URL do repositório inválida.")
            return

        # 2. Configuração do deploy
        deploy_dir = self.output_dir
        branch = 'gh-pages'
        temp_git_dir = deploy_dir / ".git"

        click.echo(f"\n🚀 Iniciando deploy do conteúdo de {deploy_dir} para {branch}...")

        try:
            # Limpa qualquer repo Git anterior dentro de page/
            if temp_git_dir.is_dir():
                shutil.rmtree(temp_git_dir)
                logger.info("Diretório .git temporário anterior removido.")
            
            # --- Sequência de comandos Git dentro da pasta 'page/' ---
            
            # Inicializa um novo repositório Git
            _run_command(['git', 'init'], cwd=deploy_dir, error_message="Falha ao inicializar Git.")

            # Adiciona o remote
            _run_command(['git', 'remote', 'add', 'origin', repo_url], cwd=deploy_dir, error_message="Falha ao adicionar remote.")

            # Adiciona todos os arquivos e faz o commit
            _run_command(['git', 'add', '-A'], cwd=deploy_dir, error_message="Falha ao adicionar arquivos.")
            _run_command(['git', 'commit', '-m', 'Deploy LinkBio: ' + Path.cwd().name], 
                         cwd=deploy_dir, error_message="Falha ao commitar arquivos.")

            # Força o push para o branch gh-pages (cria se não existir)
            # -u define a branch remota; master:gh-pages garante que a branch local 'master' 
            # (ou 'main' se for o caso do init) seja mapeada para 'gh-pages' no remote.
            # O '--force' é crucial para sobrescrever o histórico da gh-pages (que é o que queremos com build artifacts).
            _run_command(['git', 'push', '-u', 'origin', 'master:' + branch, '--force'], 
                         cwd=deploy_dir, 
                         error_message=f"Falha ao fazer push para {branch}. Verifique suas credenciais Git/GitHub.")

            click.echo(f"\n✅ Deploy para o branch '{branch}' concluído com sucesso!")
            click.echo("   Pode levar alguns minutos para que sua página esteja online.")
            
        except Exception:
            # Se qualquer comando falhar, o erro já foi reportado em _run_command.
            pass
            
        finally:
            # 3. Limpeza: remove o repositório Git temporário da pasta 'page/'
            if temp_git_dir.is_dir():
                try:
                    shutil.rmtree(temp_git_dir)
                    logger.info("Limpeza do diretório .git temporário finalizada.")
                except Exception as e:
                    logger.error(f"Falha na limpeza do .git temporário: {e}")

@click.group()
def cli():
    """linkbio - Gerador de páginas 'link in bio' estáticas."""
    pass

@cli.command()
@click.option('-p', '--path', default='.', help='Diretório raiz do projeto.')
def start(path):
    """
    Inicializa um novo projeto LinkBio: cria 'linkbio.yaml', 'assets/' e 'templates/'.
    """
    root_dir = Path(path).resolve()
    generator = LinkBioGenerator(root_dir)
    try:
        generator.start()
    except Exception as e:
        click.echo(f"\n❌ Falha grave no start: Não foi possível baixar todos os arquivos ou criar a estrutura. Erro: {e}")
        logger.critical(f"Falha na inicialização: {e}")

@cli.command()
@click.option('-p', '--path', default='.', help='Diretório raiz do projeto (onde está o linkbio.yaml).')
def build(path):
    """
    Cria a pasta 'page/' e gera os arquivos estáticos (HTML, CSS, JS) e copia os assets.
    """
    root_dir = Path(path).resolve()
    generator = LinkBioGenerator(root_dir)
    generator.build()

@cli.command()
@click.option('-p', '--port', default=8080, type=int, help='Porta para rodar o webserver de preview.')
@click.option('--path', default='.', help='Diretório raiz do projeto.')
def preview(port, path):
    """
    Roda o build e inicia um webserver simples para visualização da página gerada.
    """
    root_dir = Path(path).resolve()
    generator = LinkBioGenerator(root_dir)
    
    click.echo("🛠️ Executando build antes do preview...")
    generator.build()
    
    web_dir = generator.output_dir # 'page/'
    
    if not web_dir.is_dir():
         click.echo(f"❌ Erro: Diretório de build não encontrado em {web_dir}. Execute 'linkbio build' primeiro.")
         return

    Handler = http.server.SimpleHTTPRequestHandler
    original_cwd = os.getcwd()

    try:
        os.chdir(web_dir) 
        with socketserver.TCPServer(("", port), Handler) as httpd:
            click.echo(f"\n🚀 Servidor de preview rodando em: http://127.0.0.1:{port}")
            click.echo("   Pressione Ctrl+C para sair...")
            logger.info(f"Servidor de preview iniciado na porta {port}, servindo de {web_dir}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        click.echo("\n👋 Servidor interrompido.")
        logger.info("Servidor de preview interrompido pelo usuário.")
    except Exception as e:
        click.echo(f"❌ Erro ao iniciar o servidor: {e}")
        logger.error(f"Erro no servidor de preview: {e}")
    finally:
        os.chdir(original_cwd)
        logger.info("Limpeza do diretório de trabalho concluída.")

@cli.command()
@click.option('--path', default='.', help='Diretório raiz do projeto.')
def publish(path):
    """
    Roda o build e faz o deploy do diretório 'page/' para a branch 'gh-pages'.
    """
    root_dir = Path(path).resolve()
    generator = LinkBioGenerator(root_dir)
    try:
        generator.publish()
    except Exception as e:
        logger.error(f"Falha no comando publish: {e}")
        # A mensagem de erro principal já foi exibida por _run_command
        if not isinstance(e, subprocess.CalledProcessError) and not isinstance(e, FileNotFoundError):
             click.echo("❌ O comando de publicação falhou. Verifique os logs.")

def main():
    cli()

if __name__ == "__main__":
    main()