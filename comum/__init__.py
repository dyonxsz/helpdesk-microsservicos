"""Código compartilhado pelos microsserviços do HelpDesk.

Fica fora de `servicos/` de propósito: tokens, erros e cabeçalhos de segurança
precisam ser idênticos em todos os serviços. Cada imagem Docker copia esta
pasta junto com o serviço.
"""
