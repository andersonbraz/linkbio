import click
import logging
import yaml
import http.server
import socketserver
import os
from pathlib import Path
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader

# --- Configuração Inicial de Logging e Diretórios ---

# Define o diretório de logs no diretório de execução atual
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

# --- Gerador de LinkBio (Refatorado) ---

class LinkBioGenerator:
    """
    Gera arquivos de uma página "link in bio" usando config YAML e templates Jinja2.
    """
    
    TEMPLATE_DIR = Path(__file__).parent / "templates"
    OUTPUT_DIR_NAME = "page"
    
    def __init__(self, root_dir: Path):
        # O diretório raiz agora é obrigatório (padrão é CWD)
        self.root_dir = root_dir 
        # A pasta de saída não é criada aqui, será criada no build.
        self.output_dir = self.root_dir / self.OUTPUT_DIR_NAME
        
        # Configuração do Jinja2
        self.env = Environment(loader=FileSystemLoader(self.TEMPLATE_DIR))
        
        logger.info(f"Gerador inicializado. Diretório raiz: {self.root_dir}")

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

    def _write_file(self, file_path: Path, content: str) -> None:
        """Escreve conteúdo em um arquivo, com logging."""
        try:
            # path.write_text é uma forma limpa de escrever
            file_path.write_text(content, encoding='utf-8') 
            logger.info(f"Arquivo criado com sucesso: {file_path}")
        except IOError as e:
            logger.error(f"Erro ao criar arquivo {file_path}: {e}")
            raise

    def start(self) -> None:
        """
        FUNÇÃO CORRIGIDA: Apenas cria o arquivo 'linkbio.yaml'. 
        Não cria diretórios 'assets' ou 'page'.
        """
        logger.info("Iniciando start do LinkBio...")

        # Conteúdo do YAML de configuração (Mantido o seu exemplo)
        yaml_content = """username: 'andersonbraz_coder'
title: 'LinkBio - Anderson Braz'
avatar: 'https://avatars.githubusercontent.com/u/1479033?s=400&u=8b677aed22d26ab5b6d5fe84d9ae73a9c02143e8&v=4'
url: 'https://andersonbraz.github.io/bio/'
description: 'Project git-pages with LinkBio.'
name_author: 'Anderson Braz'
url_author: 'https://andersonbraz.com'

nav:
  - text: 'Documentação'
    url: 'https://andersonbraz.github.io'
  - text: 'Blog'
    url: 'https://andersonbraz.com'
  - text: 'Credenciais'
    url: 'https://www.credly.com/users/andersonbraz/badges'
    
social:
  - icon: 'logo-github'
    url: 'https://github.com/andersonbraz'
  - icon: 'logo-instagram'
    url: 'https://instagram.com/andersonbraz_coder'
  - icon: 'logo-youtube'
    url: 'https://youtube.com/@andersonbraz_coder'
  - icon: 'logo-linkedin'
    url: 'https://linkedin.com/in/anderson-braz'
"""

        # Escreve o arquivo YAML
        yaml_path = self.root_dir / "linkbio.yaml"
        self._write_file(yaml_path, yaml_content)

        logger.info("Start concluído.")
        click.echo(f"✅ Start concluído! Arquivo 'linkbio.yaml' criado em: {self.root_dir}")
        click.echo("💡 Agora edite o 'linkbio.yaml' e execute 'linkbio build'.")


    def build(self) -> None:
        """
        FUNÇÃO CORRIGIDA: Cria os diretórios 'assets' e 'page' e gera os arquivos estáticos.
        """
        logger.info("Iniciando build do LinkBio...")

        # 1. Cria diretórios 'assets' e 'page'
        assets_dir = self.root_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"Diretórios 'assets' e 'page' criados/verificados.")

        try:
            config = self._load_config()
        except (FileNotFoundError, yaml.YAMLError, ValueError):
            click.echo("❌ Falha no build: Verifique os logs e o arquivo linkbio.yaml.")
            return

        # Renderiza e escreve o HTML
        html_template = self.env.get_template("index.html.jinja2")
        html_content = html_template.render(**config)
        self._write_file(self.output_dir / "index.html", html_content)
        
        # Renderiza e escreve o CSS 
        css_template = self.env.get_template("style.css.jinja2")
        css_content = css_template.render()
        self._write_file(self.output_dir / "style.css", css_content)
        
        # Renderiza e escreve o JS
        js_template = self.env.get_template("script.js.jinja2")
        js_content = js_template.render()
        self._write_file(self.output_dir / "script.js", js_content)

        logger.info("Build concluído.")
        click.echo(f"✅ Build concluído! Arquivos gerados em: {self.output_dir}")
        click.echo("💡 Use 'linkbio preview' para visualizar a página.")

# --- Comandos CLI com Click (Ajustados) ---

@click.group()
def cli():
    """linkbio - Gerador de páginas 'link in bio' estáticas."""
    pass

@cli.command()
@click.option('-p', '--path', default='.', help='Diretório raiz do projeto.')
def start(path):
    """
    Inicializa um novo projeto LinkBio no PATH.
    Cria apenas o arquivo 'linkbio.yaml' de exemplo.
    """
    root_dir = Path(path).resolve()
    generator = LinkBioGenerator(root_dir)
    generator.start()

@cli.command()
@click.option('-p', '--path', default='.', help='Diretório raiz do projeto (onde está o linkbio.yaml).')
def build(path):
    """
    Cria os diretórios 'assets/' e 'page/' e gera os arquivos estáticos.
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
    
    # 1. Executa o build primeiro (que agora garante a existência dos diretórios)
    click.echo("🛠️ Executando build antes do preview...")
    generator.build()
    
    # 2. Configura e inicia o servidor
    web_dir = generator.output_dir # 'page/'
    
    # Configuração do servidor
    Handler = http.server.SimpleHTTPRequestHandler
    original_cwd = os.getcwd()

    try:
        # Muda o diretório de trabalho para 'page' para servir os arquivos corretamente
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
        os.chdir(original_cwd) # Volta ao diretório original
        logger.info("Limpeza do diretório de trabalho concluída.")


if __name__ == "__main__":
    cli()