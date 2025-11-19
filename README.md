# LinkBio

## Create Folder

```shell
mkdir bio && cd bio
```

## Start .env Python

```shell
python -m venv .venv
source .venv\bin\activate
python -m pip install --upgrade pip
```

## Install

```shell
pip install linkbio
```

```shell
linkbio start
```

## Set Infos

Edit file **linkbio.yaml** with your informations.

Example:

```yaml
username: 'andersonbraz_coder'
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
```

## Preview Page

```shell
linkbio preview --port 8000
```

## Build Page

```shell
linkbio build
```

## Publish Page

```shell
linkbio publish
```

## Example

[https://andersonbraz.github.io/linkbio/](https://andersonbraz.github.io/linkbio/)