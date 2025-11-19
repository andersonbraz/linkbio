# Arquivo: tests/test_generator.py

import pytest
import yaml
import shutil
from pathlib import Path
from unittest import mock

from src.linkbio import LinkBioGenerator 

# --- Fixtures de Ajuda ---

@pytest.fixture
def mock_yaml_content():
    """Conteúdo YAML válido para o teste de _load_config."""
    return """
username: 'test_user'
title: 'Test Bio'
nav:
  - text: 'Link 1'
    url: 'http://link1.com'
"""

@pytest.fixture
def generator_instance(tmp_path: Path):
    """Retorna uma instância de LinkBioGenerator com um diretório raiz temporário, 
    usando o fixture 'tmp_path' do pytest."""
    # Garante que o diretório de templates exista para a inicialização do Jinja2
    (tmp_path / "templates").mkdir(exist_ok=True)
    return LinkBioGenerator(root_dir=tmp_path)

# ----------------------------------------------------------------------
# TESTES DO MÉTODO: _load_config()
# ----------------------------------------------------------------------

def test_load_config_success(generator_instance, tmp_path: Path, mock_yaml_content):
    """Verifica se o carregamento de uma configuração YAML válida funciona e retorna um dict."""
    yaml_path = tmp_path / "linkbio.yaml"
    yaml_path.write_text(mock_yaml_content, encoding='utf-8')
    
    config = generator_instance._load_config()
    
    assert isinstance(config, dict)
    assert config['username'] == 'test_user'
    assert len(config['nav']) == 1

def test_load_config_file_not_found(generator_instance):
    """Verifica se levanta FileNotFoundError quando linkbio.yaml está faltando."""
    with pytest.raises(FileNotFoundError, match="linkbio.yaml não encontrado"):
        generator_instance._load_config()

def test_load_config_invalid_yaml(generator_instance, tmp_path: Path):
    """Verifica se levanta YAMLError quando o YAML está mal formatado."""
    yaml_path = tmp_path / "linkbio.yaml"
    # YAML inválido (indentação errada)
    yaml_path.write_text("chave:\n  - item1\nchave2: valor", encoding='utf-8') 
    
    with pytest.raises(yaml.YAMLError):
        generator_instance._load_config()

def test_load_config_empty_or_non_dict(generator_instance, tmp_path: Path):
    """Verifica se levanta ValueError quando o YAML não é um dicionário raiz (ex: lista ou vazio)."""
    yaml_path = tmp_path / "linkbio.yaml"
    
    # Teste para conteúdo vazio
    yaml_path.write_text("", encoding='utf-8')
    with pytest.raises(ValueError, match="não é um dicionário válido"):
        generator_instance._load_config()

# ----------------------------------------------------------------------
# TESTES DO MÉTODO: _write_file()
# ----------------------------------------------------------------------

def test_write_file_success(generator_instance, tmp_path: Path):
    """Verifica se o conteúdo é escrito corretamente no caminho especificado."""
    file_path = tmp_path / "output.txt"
    content = "Este é um conteúdo de teste."
    
    generator_instance._write_file(file_path, content)
    
    assert file_path.exists()
    assert file_path.read_text(encoding='utf-8') == content

# ----------------------------------------------------------------------
# TESTES DO MÉTODO: _copy_assets_to_output()
# ----------------------------------------------------------------------

def test_copy_assets_to_output_success(generator_instance, tmp_path: Path):
    """Verifica se o diretório assets/ é copiado corretamente para page/assets/."""
    # 1. Setup: Cria a estrutura de assets simulada
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "imagem.jpg").touch()
    (assets_dir / "subfolder").mkdir()
    (assets_dir / "subfolder" / "icon.svg").touch()
    
    # 2. Execução
    generator_instance._copy_assets_to_output()
    
    # 3. Verificação
    copied_assets_dir = tmp_path / "page" / "assets"
    assert copied_assets_dir.is_dir()
    assert (copied_assets_dir / "imagem.jpg").exists()
    assert (copied_assets_dir / "subfolder" / "icon.svg").exists()
    
def test_copy_assets_to_output_removes_old(generator_instance, tmp_path: Path):
    """Verifica se o diretório page/assets antigo é removido antes da cópia do novo."""
    # 1. Setup: Cria a estrutura de assets simulada (fonte) e um assets antigo (destino)
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "novo.jpg").touch()
    
    copied_assets_dir = tmp_path / "page" / "assets"
    copied_assets_dir.mkdir(parents=True)
    (copied_assets_dir / "antigo.txt").touch() # Arquivo antigo que deve ser removido
    
    # 2. Execução
    generator_instance._copy_assets_to_output()
    
    # 3. Verificação
    # Verifica se o arquivo antigo foi removido
    assert not (copied_assets_dir / "antigo.txt").exists()
    # Verifica se o novo arquivo foi copiado
    assert (copied_assets_dir / "novo.jpg").exists()

# ----------------------------------------------------------------------
# TESTES DO MÉTODO: build() (INTEGRAÇÃO E MOCKING DO JINJA2)
# ----------------------------------------------------------------------

# Usamos mock.patch para simular o carregamento da config (isolamento)
@mock.patch('linkbio.LinkBioGenerator._load_config') 
def test_build_full_flow(mock_load_config, generator_instance, tmp_path: Path):
    """Testa o fluxo completo do build, simulando a renderização e verificando a cópia de assets."""
    
    # 1. Setup
    mock_load_config.return_value = {'title': 'Full Flow Test'}
    
    # Simula a existência de um arquivo asset
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "test_asset.txt").touch()

    # 2. Mocking do Jinja2 para simular o conteúdo renderizado
    # Mockamos 'get_template' no ambiente (env) da instância do generator.
    with mock.patch.object(generator_instance.env, 'get_template') as mock_get_template:
        
        # Cria um Mock de template que retorna um valor fixo ao ser renderizado
        mock_template = mock.Mock()
        mock_template.render.return_value = "Rendered Content"
        mock_get_template.return_value = mock_template 

        # 3. Execução
        generator_instance.build()

        # 4. Verificação dos Resultados
        output_dir = tmp_path / "page"
        copied_assets_dir = output_dir / "assets"
        
        # Arquivos de saída criados e com o conteúdo simulado
        assert (output_dir / "index.html").read_text(encoding='utf-8') == "Rendered Content"
        assert (output_dir / "style.css").read_text(encoding='utf-8') == "Rendered Content"
        assert (output_dir / "script.js").read_text(encoding='utf-8') == "Rendered Content"
        
        # Verifica se o Jinja2 foi chamado para renderizar 3 arquivos
        assert mock_template.render.call_count == 3
        
        # Verifica se a configuração foi passada na primeira chamada (que é o index.html)
        html_render_call_args = mock_template.render.call_args_list[0][0][0]
        assert html_render_call_args['title'] == 'Full Flow Test'
        
        # Assets copiados corretamente (Teste de integração da cópia de diretório)
        assert copied_assets_dir.is_dir()
        assert (copied_assets_dir / "test_asset.txt").exists()