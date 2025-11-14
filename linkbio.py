import click
import logging
import yaml
import http.server
import socketserver
import os
import requests
import shutil # Adicionado para copiar assets
from pathlib import Path
from typing import Dict, Any
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

# --- Constantes para URLs e Arquivos ---

# Usamos a URL 'raw' para obter o conteúdo dos arquivos diretamente
GITHUB_BASE_URL = "https://raw.githubusercontent.com/andersonbraz/linkbio/main"

ASSET_FILES = [
    "bg-desktop-light.jpg",
    "bg-desktop.jpg",
    "bg-mobile-light.jpg",
    "bg-mobile.jpg",
    "moon-stars.svg",
    "sun.svg"
    "verified.svg"
]

TEMPLATE_FILES = [
    "index.html.jinja2",
    "script.js.jinja2",
    "style.css.jinja2"
]


# --- Gerador de LinkBio ---

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
        
        # O Jinja2 carregará os templates da pasta criada no 'start'
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        
        logger.info(f"Gerador inicializado. Diretório raiz: {self.root_dir}")

    # Método auxiliar para download de arquivos binários/texto
    def _download_file(self, url: str, destination_path: Path) -> None:
        """Faz o download de um arquivo de uma URL e salva no destino."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status() # Lança exceção para códigos de status ruins
            
            # Use 'wb' para garantir que imagens/SVGs sejam tratados corretamente (binário)
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

    # Método auxiliar para escrita de texto (apenas para YAML)
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
        
        # --- 1. Cria diretórios ---
        self.assets_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        click.echo(f"📁 Diretórios 'assets' e 'templates' criados.")

        # --- 2. Cria arquivo YAML ---
        yaml_content = """username: 'andersonbraz_coder'
title: 'LinkBio - Anderson Braz'
avatar: 'https://avatars.githubusercontent.com/u/1479033?s=400&u=8b677aed22d26ab5b6d5fe84d9ae73a9c02143e8&v=4'
url: 'https://andersonbraz.github.io/bio/'
description: 'Project git-pages with LinkBio.'
name_author: 'Anderson Braz'
url_author: 'https://andersonbraz.com'
fav_icon: 'href="https://github.githubassets.com/favicons/favicon-dark.png"'

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
        yaml_path = self.root_dir / "linkbio.yaml"
        self._write_file(yaml_path, yaml_content)

        # --- 3. Download de Assets ---
        click.echo("⬇️ Baixando Assets...")
        for filename in ASSET_FILES:
            url = f"{GITHUB_BASE_URL}/assets/{filename}"
            destination = self.assets_dir / filename
            self._download_file(url, destination)

        # --- 4. Download de Templates ---
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
            # 1. Garante que o diretório 'page' existe
            self.output_dir.mkdir(exist_ok=True) 

            # 2. Se o destino já existe (page/assets), ele deve ser removido antes de copytree
            if destination_dir.exists():
                shutil.rmtree(destination_dir)
                logger.info(f"Diretório antigo {destination_dir} removido.")
            
            # 3. Copia recursivamente a pasta assets/ para page/assets
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

        # 1. Cria diretório 'page' (ou garante que exista)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"Diretório 'page' criado/verificado.")

        try:
            config = self._load_config()
        except (FileNotFoundError, yaml.YAMLError, ValueError):
            click.echo("❌ Falha no build: Verifique os logs e o arquivo linkbio.yaml.")
            return

        # 2. Renderiza e escreve os arquivos (Otimizado)
        try:
            html_template = self.env.get_template("index.html.jinja2")
            css_template = self.env.get_template("style.css.jinja2")
            js_template = self.env.get_template("script.js.jinja2")

            self._write_file(self.output_dir / "index.html", html_template.render(**config))
            self._write_file(self.output_dir / "style.css", css_template.render())
            self._write_file(self.output_dir / "script.js", js_template.render())
            
            # 3. Copia assets para a pasta de build (page/assets)
            self._copy_assets_to_output() 
            
            logger.info("Build concluído.")
            click.echo(f"✅ Build concluído! Arquivos gerados em: {self.output_dir}")
            click.echo("💡 Use 'linkbio preview' para visualizar a página.")

        except Exception as e:
            logger.error(f"Erro durante a renderização ou escrita: {e}")
            click.echo(f"❌ Erro durante o build: {e}")

# --- Comandos CLI com Click ---

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
    
    # 1. Executa o build primeiro
    click.echo("🛠️ Executando build antes do preview...")
    generator.build()
    
    # 2. Configura e inicia o servidor
    web_dir = generator.output_dir # 'page/'
    
    if not web_dir.is_dir():
         click.echo(f"❌ Erro: Diretório de build não encontrado em {web_dir}. Execute 'linkbio build' primeiro.")
         return

    # Usando o SimpleHTTPRequestHandler para servir arquivos
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